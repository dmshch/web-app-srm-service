# web-app-srm-service
WebAppSrmService - a web application based Flask (Python 3). The service displays signal parameters received from satellite receivers (the application for polling receivers and saving the results to the database are here - https://github.com/dmshch/srm-service; WebAppSrmService only displays the retrieved data from the database table).

##### Displayed signal parameters:

* C/N (dB)
* Eb/NO(dB)
* Link Margin (dB)
* Program Number for output (SDI and IP)
* CC Errors for output services, delta between updates (Δ)(for ProView 7100 old firmware < 4.0 - N/A)
