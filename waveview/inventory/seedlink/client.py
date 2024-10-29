import logging
from pathlib import Path
from urllib.parse import urlparse

import lxml
from django.conf import settings
from django.db import connection
from obspy.clients.seedlink.client.seedlinkconnection import SeedLinkConnection
from obspy.clients.seedlink.client.slstate import SLState
from obspy.clients.seedlink.slpacket import SLPacket

from waveview.inventory.db.schema import TimescaleSchemaEditor

logger = logging.getLogger(__name__)

STATE_FILE = settings.RUN_DIR / "seedlink.state"


def get_statefile() -> Path:
    return STATE_FILE


class EasySeedLinkClientException(Exception):
    """
    A base exception for all errors triggered explicitly by EasySeedLinkClient.
    """

    pass


class EasySeedLinkClient:
    """
    An easy-to-use SeedLink client.
    """

    def __init__(
        self, server_url: str, autoconnect: bool = True, debug: bool = False
    ) -> None:
        # Allow for sloppy server URLs (e.g. 'geofon.gfz-potsdam.de:18000).
        # (According to RFC 1808 the net_path segment needs to start with '//'
        # and this is expected by the urlparse function, so it is silently
        # added if it was omitted by the user.)
        if "://" not in server_url and not server_url.startswith("//"):
            server_url = "//" + server_url

        parsed_url = urlparse(server_url, scheme="seedlink")

        # Check the provided scheme
        if not parsed_url.scheme == "seedlink":
            msg = 'Unsupported scheme %s (expected "seedlink")' % parsed_url.scheme
            raise EasySeedLinkClientException(msg)
        if not parsed_url.hostname:
            msg = "No host name provided"
            raise EasySeedLinkClientException(msg)

        self.server_hostname = parsed_url.hostname
        self.server_port = parsed_url.port or 18000
        self.debug = debug

        self.conn = SeedLinkConnection()

        self.conn.set_sl_address("%s:%d" % (self.server_hostname, self.server_port))
        logger.info(
            "Connecting to SeedLink server %s:%d"
            % (self.server_hostname, self.server_port)
        )

        if autoconnect:
            self.connect()

        # A flag to indicate if the client has entered streaming mode
        self.__streaming_started = False

        self.__capabilities = None

        self.schema = TimescaleSchemaEditor(connection=connection)

    def connect(self) -> None:
        """
        Connect to the SeedLink server.
        """
        self.conn.connect()
        self.conn.state.state = SLState.SL_UP

    def get_info(self, level: str) -> str:
        """
        Send a SeedLink ``INFO`` command and retrieve response.

        Available info levels depend on the server implementation. Usually one
        of ``ID``, ``CAPABILITIES``, ``STATIONS``, ``STREAMS``, ``GAPS``,
        ``CONNECTIONS``, ``ALL``.

        As a convenience, the server's ``CAPABILITIES`` can be accessed through
        the client's :attr:`~.EasySeedLinkClient.capabilities` attribute.

        .. note::

            This is a synchronous call. While the client waits for the
            response, other packets the server might potentially send will
            be disregarded.

        :type level: str
        :param level: The INFO level to retrieve (sent as ``INFO:LEVEL``)
        """
        if self.__streaming_started:
            msg = (
                "Method not available after SeedLink connection has "
                + "entered streaming mode."
            )
            raise EasySeedLinkClientException(msg)

        # Send the INFO request
        self.conn.request_info(level)

        # Wait for full response
        while True:
            data = self.conn.collect()

            if data == SLPacket.SLTERMINATE:
                msg = (
                    "SeedLink connection terminated while expecting " + "INFO response"
                )
                raise EasySeedLinkClientException(msg)
            elif data == SLPacket.SLERROR:
                msg = "Unknown error occured while expecting INFO response"
                raise EasySeedLinkClientException(msg)

            # Wait for the terminated INFO response
            packet_type = data.get_type()
            if packet_type == SLPacket.TYPE_SLINFT:
                return self.conn.get_info_string()

    @property
    def capabilities(self) -> list[str]:
        """
        The server's capabilities, parsed from ``INFO:CAPABILITIES`` (cached).
        """
        if self.__capabilities is None:
            self.__capabilities = []

            capabilities_xml = self.get_info("CAPABILITIES")

            # The INFO response should be encoded in UTF-8. However, if the
            # encoding is given in the XML header (e.g. by IRIS Ringserver),
            # lxml accepts byte input only (and raises a ValueError otherwise.)
            #
            # Example XML header with encoding:
            #     <?xml version="1.0" encoding="utf-8"?>
            try:
                root = lxml.etree.fromstring(capabilities_xml)
            except ValueError:
                root = lxml.etree.fromstring(capabilities_xml.encode("UTF-8"))

            nodes = root.findall("capability")

            for node in nodes:
                self.__capabilities.append(node.attrib["name"].lower())

        return self.__capabilities

    def has_capability(self, capability: str) -> bool:
        """
        Check if the SeedLink server has a certain capability.

        The capabilities are fetched using an ``INFO:CAPABILITIES`` request.

        :type capability: str
        :param capability: The capability to check for

        :rtype: bool
        :return: Whether the server has the given capability
        """
        return capability.lower() in self.capabilities

    def has_info_capability(self, capability: str) -> bool:
        """
        A shortcut for checking for ``INFO`` capabilities.

        Calling this is equivalent to calling
        :meth:`~.EasySeedLinkClient.has_capability`
        with ``'info:' + capability``.

        .. rubric:: Example

        .. code-block:: python

            # Check if the server has the INFO:STREAMS capability
            client.has_info_capability('STREAMS')

        :type capability: str
        :param capability: The ``INFO`` capability to check for

        :rtype: bool
        :return: Whether the server has the given ``INFO`` capability
        """
        return self.has_capability("info:" + capability)

    def _send_and_recv(self, bytes_: bytes, stop_on: list[bytes] = [b"END"]) -> bytes:
        """
        Send a command to the server and read the response.

        The response is read until a packet is received that ends with one of
        the provided stop words.

        .. warning::

            If the server doesn't send one of the stop words, this never
            returns!

        :type bytes_: bytes
        :param bytes_: The bytes to send to the server
        :type stop_on: list[str]
        :param stop_on: A list of strings that indicate the end of the server
                        response.

        :rtype: bytes
        :return: The server's response
        """
        if not bytes_.endswith(b"\r"):
            bytes_ += b"\r"
        if not type(stop_on) is list:
            stop_on = [stop_on]
        for i, stopword in enumerate(stop_on):
            if not isinstance(stopword, bytes):
                stop_on[i] = stopword.encode()

        self.conn.socket.send(bytes_)

        response = bytearray()
        while True:
            bytes_read = self.conn.socket.recv(SeedLinkConnection.DFT_READBUF_SIZE)
            if not bytes_read:
                break
            response += bytes_read
            for stopword in stop_on:
                if response.endswith(stopword):
                    # Collapse the bytearray
                    return bytes(response)

    def _get_cat(self) -> bytes:
        """
        Send the CAT command to a server and receive the answer.

        This can potentially be used for older SeedLink servers that don't
        support the ``INFO:STREAMS`` command yet.
        """
        # Quick hack, but works so far
        ringserver_error = "CAT command not implemented\r\n"

        response = self._send_and_recv("CAT", ["END", ringserver_error])

        if response == ringserver_error:
            raise EasySeedLinkClientException(ringserver_error.strip())

        return response

    def select_stream(
        self, net: str, station: str, selector: str | None = None
    ) -> None:
        """
        Select a stream for data transfer.

        This method can be called once or multiple times as needed. A
        subsequent call to the :meth:`~.EasySeedLinkClient.run` method starts
        the streaming process.

        .. note::
            Selecting a stream always puts the SeedLink connection in
            *multi-station mode*, even if only a single stream is selected.
            *Uni-station mode* is not supported.

        :type net: str
        :param net: The network id
        :type station: str
        :param station: The station id
        :type selectors: str
        :param selector: a valid SeedLink selector, e.g. ``EHZ`` or ``EH?``
        """
        if not self.has_capability("multistation"):
            msg = "SeedLink server does not support multi-station mode"
            raise EasySeedLinkClientException(msg)

        if self.__streaming_started:
            msg = (
                "Adding streams is not supported after the SeedLink "
                + "connection has entered streaming mode."
            )
            raise EasySeedLinkClientException(msg)

        self.conn.add_stream(net, station, selector, seqnum=-1, timestamp=None)

    def set_state_file(self, statefile: str) -> None:
        """
        Set the state file for the SeedLink connection.

        The state file is used to store the state of the SeedLink connection
        (e.g. selected streams, sequence numbers, etc.) between runs. This
        allows the client to resume streaming without having to reselect
        streams.

        :type filename: str
        :param filename: The path to the state file
        """
        self.conn.set_state_file(statefile)

    def run(self) -> None:
        """
        Start streaming data from the SeedLink server.

        Streams need to be selected using
        :meth:`~.EasySeedLinkClient.select_stream` before this is called.

        This method enters an infinite loop, calling the client's callbacks
        when events occur.
        """
        # Note: This somewhat resembles the run() method in SLClient.

        # Check if any streams have been specified (otherwise this will result
        # in an infinite reconnect loop in the SeedLinkConnection)
        if not len(self.conn.streams):
            msg = "No streams specified. Use select_stream() to select a stream."
            raise EasySeedLinkClientException(msg)

        self.__streaming_started = True

        # Start the collection loop
        while True:
            data = self.conn.collect()

            if data == SLPacket.SLTERMINATE:
                self.on_terminate()
                break
            elif data == SLPacket.SLERROR:
                self.on_seedlink_error()
                continue

            # At this point the received data should be a SeedLink packet
            # XXX In SLClient there is a check for data == None, but I think
            #     there is no way that self.conn.collect() can ever return None
            assert isinstance(data, SLPacket)

            packet_type = data.get_type()

            # Ignore in-stream INFO packets (not supported)
            if packet_type not in (SLPacket.TYPE_SLINF, SLPacket.TYPE_SLINFT):
                # Pass the trace to the on_data callback
                self.on_data(data)

    def close(self) -> None:
        """
        Close the SeedLink connection.

        .. note::

            Closing  the connection is not threadsafe yet. Client code must
            ensure that :meth:`~.EasySeedLinkClient.run` and
            :meth:`SeedLinkConnection.terminate()
            <obspy.clients.seedlink.client.seedlinkconnection.SeedLinkConnection.terminate>`
            are not being called after the connection has been closed.

            See the corresponding `GitHub issue
            <https://github.com/obspy/obspy/pull/876#issuecomment-60537414>`_
            for details.
        """
        self.conn.disconnect()

    def on_terminate(self) -> None:
        """
        Callback for handling connection termination.

        A termination event can either be triggered by the SeedLink server
        explicitly terminating the connection (by sending an ``END`` packet in
        streaming mode) or by the
        :meth:`~obspy.clients.seedlink.client.seedlinkconnection.SeedLinkConnection.terminate`
        method of the
        :class:`~obspy.clients.seedlink.client.seedlinkconnection.SeedLinkConnection`
        object being called.
        """
        pass

    def on_seedlink_error(self) -> None:
        """
        Callback for handling SeedLink errors.

        This handler is called when an ``ERROR`` response is received. The
        error generally corresponds to the last command that was sent to the
        server. However, with the current implementation of the SeedLink
        connection, no further information about the error is available.
        """
        pass

    def on_data(self, packet: SLPacket) -> None:
        """
        Callback for handling the reception of waveform data.

        Override this for data streaming.

        :type trace: :class:`~obspy.core.trace.Trace`
        :param trace: The trace received from the server
        :type packet: :class:`~obspy.clients.seedlink.slpacket.SLPacket`
        """
        pass
