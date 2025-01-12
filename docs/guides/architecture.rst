============
Architecture
============

Data Model

All data is managed within organization scope. When a user registers in the
system, it has to be added to the organization to allow the user view or manage
organization resources. Hence, each user has a certain role within the
organization and each role binds to certain permissions.

When an organization is created, default inventory associated with the
organization is also created. Inventory stores list of seismic networks. A
seismic network has many stations, and each station has typically 3 channels (Z,
N, E).

Organization admin can create the inventory in two ways in the admin panel.
First, creating a network, station, and channel one by one or by uploading a
StationXML file containing the inventory info. The latter should be more
convenient as the StationXML file is also used by SeisComP. After uploading the
StationXML file, the system will automatically parse the info and store it in
the database.

When the channel is created, the system automatically creates a data stream
table to store the waveform data. This data stream is stored in chunks when the
Seedlink packet is received by the acquisition service. The system also uses
data compression to reduce the size of the chunk. When another process wants to
query the data stream, the system will decompress back to the original data.

Organization contains one or more volcanoes to be monitored. When a volcano is
created, the system will create a default catalog. Catalog is the collection of
the picked seismic events. Each event contains a lot of info such as time,
duration, event type, amplitude, magnitude, location, attachment and more.

In addition to that, the app can be customized based on the preferred
configuration. For the current version, the user can create its own picker
configuration, filter set, and default resources to display.

In the future version, other features can be added such as auto-picking,
hypocenter relocation, spectral analysis, and AI system to provide better
classification and analysis.

Backend

The system is created using two technology stacks, backend web service and
frontend client. Two stacks communicate via REST API for managing resources and
WebSocket for real time data streaming and notification.

Backend service is primarily written using Python and Django web framework. For
persistent storage we use PostgreSQL to store relational data (organization,
volcano, catalog, event, etc) and TimescaleDB for waveform data.

Workflow

Seismic signals are primarily captured by sensors located at remote stations and
transmitted to a central server at the office through radio communication. In
the office, the Guralp Scream software handles data collection from these
streams. It not only records the data but also acts as a broadcaster, forwarding
packet data to other systems.

One of these systems, SeisComP, is a comprehensive seismological software suite
used for data acquisition, processing, distribution, and interactive analysis.
SeisComP leverages the Seedlink protocol to forward MiniSEED (msd) packets to
compatible applications, including VEPS.

The system uses the Seedlink protocol to collect data streams and store it in
TimescaleDB. The data is organized into chunks, each containing details such as
start time, end time, sample rate, and recorded data, all compressed using
Zstandard to reduce storage size.

When a user picks a new event, the system will send the notification to each
connected client. Once the client receives this notification, it fetches the
list of events within the chart extents and re-update the event marker
automatically.

In several cases, the user account that picks an event may be a bot
(autopicker). This service may annotate the event with type auto and the
observer will validate and update the right event type. The system then marks
the bot as author while the observer that validates the event will be added as a
collaborator.

The system also has a feature called event observer. When an event is created,
updated, or deleted, this class will be called with certain payload or data.
This class acts as a callback and can be used to calculate additional info about
the event. For example, calculating amplitude and magnitude, adding event
attachment (photos and videos) automatically by fetching the media API, or
calculating hypocenter location. The class can be extended by demand and can be
enabled/disabled in the admin panel.

The system also integrates externally with the Cendana15 platform and the BMA,
allowing synchronization of picked seismic events. The system can also be
extended to integrate with other systems via API.

Frontend

Frontend web client primarily written using TypeScript and React. For the UI,
the system uses a modern and mature framework from Microsoft FluentUI.
Generally, we have no problem in implementing user interface and logic, but
there are several challenges we need to solve. It includes fetching data streams
without interrupting user workflow, rendering dense signals, and handling
several signal analysis tools.

First challenge we face is that we need to display and render dense signals
without losing the shape and accuracy. To solve this issue, we  write a custom
charting library using HTML Canvas called ZCharts. There are two types of chart
available, helicorder and seismogram. ZCharts also implement additional plugins
such as event pointer, event marker display, and picking tool.

A helicorder is a type of chart used primarily in seismology to display a
continuous record of ground motion or seismic data. This chart is designed to
mimic the appearance of traditional drum-based seismographs, which would use
paper rolls inked by a stylus to record seismic events over time.

A seismogram is a type of chart used primarily in seismology to display a
continuous record of ground motion or seismic data. This chart is composed of
multiple tracks, each representing a channel of data.

The architecture of these two charts follow a model view design pattern. Each
component such as axis, grid, and track has a model to store its data and view
to represent the appearance and rendering.

Currently helicorder uses 50 sps, 30 minutes interval, and 12 hour duration.
This means that there are 2,225,000 data points in the helicorder chart. When
the user navigates the chart by shifting the view up or down, increasing or
decreasing the amplitude, we need to re-render those points.

For the seismogram chart, there are default 4 channels with a 5 minute interval
and 100 sps when the user selects a window on the helicorder. It means there are
120,000 points that need to be rendered. When users add new channels, for
example up to 10 channels, we need to render 300,000 points.

For such huge data points, rendering those points on the main thread would make
the application not responsive as it blocks the execution. To handle dense
signal rendering without freezing up the UI, we use Web Workers to offload the
rendering process on the worker thread. For 30 minutes interval and 25 sps we
observe rendering time in the range 600-700ms, while for 5 minutes interval and
100 sps, we observe rendering time in the range 50-80ms.

We also use web workers to fetch the data stream in the background so the user
won't be interrupted with loading. For example, the data workflow in the Picker
app is defined as follows. When the user opens the Picker, the app will request
a data stream for all helicorder segments if it is not already present in the
cache. The request is sent from the main thread to the worker. The worker then
sent the request packet containing request ID, time range, channel ID, and other
info via websocket to the server. The server then fetches the data stream from
the database, processes the chunk, and sends back the data stream to the client.
To reduce the data that need to be sent, the server compresses the packet using
the Zstandard algorithm. Once the packet is received in the worker, the worker
decompresses the data, sends it back to the main thread, and stores the data
stream in the helicorder. Helicorder then sends the data stream to the render
worker to render the signal via offscreen canvas. Render result in the bitmap
image is then displayed to the helicorder segment while preserving the
coordinate. When the user clicks a certain segment in the helicorder chart, a 5
minute selection window marker will appear and seismogram will display the
signal within this time range. The seismogram also requests the data stream via
a worker similar to how a helicorder segment displays the signal. By leveraging
all these technologies we could achieve much better performance while still
preserving data accuracy.

In the future version, several features can also be developed such as spectral
analysis, hypocenter picking tools, admin panel, real time chat, and AI
assistance to provide labeling and more comprehensive data insight.
