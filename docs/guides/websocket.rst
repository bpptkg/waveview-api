=============
WebSocket API
=============

WebSocket API enables real-time communication between clients and servers. It is
a full-duplex communication channel that operates over a single socket and is
ideal for applications that require real-time updates.

There are two WebSocket endpoints ``wss://<server-url>/ws/stream/`` (Stream API)
for stream related processing and ``wss://<server-url>/ws/waveview/`` (General
API) for common functionalities like notifications.

Stream API
----------

Stream API is used for streaming waveform data from the server to the client,
e.g. getting the waveform, filtering, and calculation spectrogram.

WebSocket Request

To send a message using WebSocket API, a client send a request in JSON using the
following format:

.. code-block:: typescript

    export type WebSocketCommand = 'stream.fetch' | 'stream.spectrogram' | 'stream.filter' | 'ping' | 'notify' | 'join';
    export type WebSocketMessageType = 'request' | 'response' | 'notify';
    export type WebSocketMessageStatus = 'success' | 'error';

    export interface WebSocketRequest<T = any> {
        command: WebSocketCommand;
        data: T;
    }


stream.fetch

To get the waveform data from the server, the client sends a request using the
``stream.fetch`` command. The request data should be in the following format:

.. code-block:: typescript

    export interface StreamRequestData {
        requestId: string;
        channelId: string;
        start: number;
        end: number;
        forceCenter: boolean;
        resample: boolean;
        sampleRate: number;
    }


stream.filter

To filter the waveform data from the server, the client sends a request using
the ``stream.filter`` command. The request data should be in the following format:

.. code-block:: typescript

    export type FilterType = 'bandpass' | 'lowpass' | 'highpass' | 'none';
    export type TaperType =
        | 'cosine'
        | 'barthann'
        | 'bartlett'
        | 'blackman'
        | 'blackmanharris'
        | 'bohman'
        | 'boxcar'
        | 'chebwin'
        | 'flattop'
        | 'gaussian'
        | 'general_gaussian'
        | 'hamming'
        | 'hann'
        | 'kaiser'
        | 'nuttall'
        | 'parzen'
        | 'slepian'
        | 'triang';

    export interface BandpassFilterOptions {
        freqmin: number;
        freqmax: number;
        order: number;
        zerophase: boolean;
    }

    export interface LowpassFilterOptions {
        freq: number;
        order: number;
        zerophase: boolean;
    }

    export interface HighpassFilterOptions {
        freq: number;
        order: number;
        zerophase: boolean;
    }

    export type FilterOptions = BandpassFilterOptions | LowpassFilterOptions | HighpassFilterOptions;

    export interface FilterRequestData {
        requestId: string;
        channelId: string;
        start: number;
        end: number;
        filterType: FilterType;
        filterOptions: FilterOptions;
        taperType: TaperType;
        taperWidth: number;
        resample: boolean;
        sampleRate: number;
    }

stream.spectrogram

To get the spectrogram data from the server, the client sends a request using
the ``stream.spectrogram`` command. The request data should be in the following format:

.. code-block:: typescript

    export interface SpectrogramRequestData {
        requestId: string;
        channelId: string;
        start: number;
        end: number;
        width: number;
        height: number;
        resample: boolean;
        sampleRate: number;
    }

Stream Packet

For ``stream.fetch``, ``stream.filter`` commands, the server responds to the
client request with a message in bytes using the following format:

.. code-block::

    request_id: string(64)
    command: string(64)
    channel_id: string(64)
    header:
        start: uint64
        end: uint64
        length: uint64
        time: uint64
        sample_rate: uint64
        reserved: uint64
        reserved: uint64
        reserved: uint64
    data:
        stream_data: binary data

Each packet is compressed using Zstd algorithm.

Spectrogram Packet

For ``stream.spectrogram`` command, the server responds to the client request
with a message in bytes using the following format:

.. code-block::

    request_id: string(64)
    command: string(64)
    channel_id: string(64)
    header:
        start: uint64
        end: uint64
        time_min: uint64
        time_max: uint64
        freq_min: uint64
        freq_max: uint64
        time_length: uint64
        freq_length: uint64
        min_val: float64
        max_val: float64
    data:
        image_data: binary data

Each packet is compressed using Zstd algorithm.

You can see the example for function to decode the packet in the waveview client
at `here
<https://github.com/bpptkg/waveview/blob/main/packages/web/src/shared/stream.ts>`_.
