# Resonanz Development Assessment

### TODO:

#### Backend

 - [x] Set up Flask
 - [x] Set up database
 - [x] Set up Logging
 - [x] Normalize addresses and choose best backend
   - [x] Get basic functionality with Nominatim
   - [x] Get basic functionality with Google Maps API
 - [x] Implement address matching
 - [ ] Implement loading CSVs
 - [ ] Normalize names? (use as lower for easy matching and have Capitalized for return)

#### Frontend

 - [x] Set up basic ~~HTMX~~ jQuery, bootstrap
 - [ ] Set up basic map/locator
 - [x] Implement csv batch loading and streaming to BE
 - [ ] Implement results download
 - Views:
   - [x] Home/Search
   - [x] Add address/tenant
   - ~~Some settings~~

#### Deployment

 - [x] Bare metal default (debug)
 - [x] Bare metal with WSGI
 - [ ] Docker
