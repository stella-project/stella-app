# STELLA application

# Workflow for sending feedback to the stella-app
[![](https://mermaid.ink/img/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG4gICAgc2l0ZSAtPj4gc3RlbGxhX2FwcDogR0VUIC9yYW5raW5nP3E9PHN0cmluZzpxdWVyeT5cbiAgICBOb3RlIHJpZ2h0IG9mIHN0ZWxsYV9hcHA6IDEpIHVwb24gcmVxdWVzdCBvZiBhIDxicj4gcmFua2luZyBhIG5ldyA8YnI-IHNlc3Npb24gd2lsbCBiZSB3cml0dGVuIDxicj4gdG8gdGhlIGxvY2FsIGRiXG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiAyKSBvbmUgcmFua3N5cyArIDxicj4gb25lIHJlY3N5cyA8YnI-IGFyZSBhc3NpZ25lZCB0byA8YnI-IHRoZSBzZXNzaW9uXG4gICAgc3RlbGxhX2FwcCAtLT4-IHNpdGU6IDxpdGVtcz4gPGJyPiA8YnI-ICgrIHJhbmtpbmdfaWQgKyBzZXNzaW9uX2lkKVxuICAgIE5vdGUgbGVmdCBvZiBzaXRlOiBsb2dzIHVzZXIgZGF0YSA8YnI-IGFuZCBpbnRlcmFjdGlvbnNcbiAgICBOb3RlIGxlZnQgb2Ygc2l0ZTogVXNlciBlbnRlcnMgPGJyPiBuZXcgcXVlcnlcbiAgICBzaXRlIC0-PiBzdGVsbGFfYXBwOiBHRVQgL3Jhbmtpbmc_cT0uLi4_cz1zZXNzaW9uX2lkXG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiBzdGVsbGFfYXBwIHJldHVybnMgPGJyPiBhbm90aGVyIHJhbmtpbmcgYnkgPGJyPiB0aGUgc3lzdGVtIHRoYXQgaXMgPGJyPiBhc3NpZ25lZCB0byB0aGUgPGJyPiBzZXNzaW9uIHdpdGggPGJyPiBzZXNzaW9uX2lkXG4gICAgc3RlbGxhX2FwcCAtLT4-IHNpdGU6IDxpdGVtcz4gPGJyPiA8YnI-ICgrIHJhbmtpbmdfaWQgKyBzZXNzaW9uX2lkKVxuICAgIE5vdGUgbGVmdCBvZiBzaXRlOiBsb2dzIHVzZXIgZGF0YSA8YnI-IGFuZCBpbnRlcmFjdGlvbnNcbiAgICBzaXRlIC0-PiBzdGVsbGFfYXBwOiBQT1NUIC9mZWVkYmFja3MvPHJhbmtpbmdfaWQ-XG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiBzdGVsbGFfYXBwIHdyaXRlcyA8YnI-IChjbGljaykgZmVlZGJhY2sgPGJyPiB0byBsb2NhbCBkYlxuICAgIHNpdGUgLT4-IHN0ZWxsYV9hcHA6IEdFVCBzZXNzaW9ucy88c2Vzc2lvbl9pZD4vZXhpdCBcbiAgICBOb3RlIHJpZ2h0IG9mIHN0ZWxsYV9hcHA6IE9wdGlvbmFsbHkgdGhlIDxicj4gc3RlbGxhX2FwcCBpcyBub3RpZmllZCA8YnI-IHdoZW4gc2Vzc2lvbnMgZW5kc1xuICAgIE5vdGUgcmlnaHQgb2Ygc3RlbGxhX2FwcDogc3RlbGxhX2FwcCBjaGVja3MgPGJyPiBsb2NhbCBkYiByZWd1bGFybHkgPGJyPiAoYnkgYSBnaXZlbiBpbnRlcnZhbCA8YnI-IGluIHRoZSBjb25maWctZmlsZSkgPGJyPiBhbmQgdXBsb2FkcyA8YnI-IGFsbCBlbmRlZCBzZXNzaW9ucyA8YnI-IHRvIHRoZSBzdGVsbGFfc2VydmVyXG5cbiIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2V9)](https://mermaid-js.github.io/mermaid-live-editor/#/edit/eyJjb2RlIjoic2VxdWVuY2VEaWFncmFtXG4gICAgc2l0ZSAtPj4gc3RlbGxhX2FwcDogR0VUIC9yYW5raW5nP3E9PHN0cmluZzpxdWVyeT5cbiAgICBOb3RlIHJpZ2h0IG9mIHN0ZWxsYV9hcHA6IDEpIHVwb24gcmVxdWVzdCBvZiBhIDxicj4gcmFua2luZyBhIG5ldyA8YnI-IHNlc3Npb24gd2lsbCBiZSB3cml0dGVuIDxicj4gdG8gdGhlIGxvY2FsIGRiXG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiAyKSBvbmUgcmFua3N5cyArIDxicj4gb25lIHJlY3N5cyA8YnI-IGFyZSBhc3NpZ25lZCB0byA8YnI-IHRoZSBzZXNzaW9uXG4gICAgc3RlbGxhX2FwcCAtLT4-IHNpdGU6IDxpdGVtcz4gPGJyPiA8YnI-ICgrIHJhbmtpbmdfaWQgKyBzZXNzaW9uX2lkKVxuICAgIE5vdGUgbGVmdCBvZiBzaXRlOiBsb2dzIHVzZXIgZGF0YSA8YnI-IGFuZCBpbnRlcmFjdGlvbnNcbiAgICBOb3RlIGxlZnQgb2Ygc2l0ZTogVXNlciBlbnRlcnMgPGJyPiBuZXcgcXVlcnlcbiAgICBzaXRlIC0-PiBzdGVsbGFfYXBwOiBHRVQgL3Jhbmtpbmc_cT0uLi4_cz1zZXNzaW9uX2lkXG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiBzdGVsbGFfYXBwIHJldHVybnMgPGJyPiBhbm90aGVyIHJhbmtpbmcgYnkgPGJyPiB0aGUgc3lzdGVtIHRoYXQgaXMgPGJyPiBhc3NpZ25lZCB0byB0aGUgPGJyPiBzZXNzaW9uIHdpdGggPGJyPiBzZXNzaW9uX2lkXG4gICAgc3RlbGxhX2FwcCAtLT4-IHNpdGU6IDxpdGVtcz4gPGJyPiA8YnI-ICgrIHJhbmtpbmdfaWQgKyBzZXNzaW9uX2lkKVxuICAgIE5vdGUgbGVmdCBvZiBzaXRlOiBsb2dzIHVzZXIgZGF0YSA8YnI-IGFuZCBpbnRlcmFjdGlvbnNcbiAgICBzaXRlIC0-PiBzdGVsbGFfYXBwOiBQT1NUIC9mZWVkYmFja3MvPHJhbmtpbmdfaWQ-XG4gICAgTm90ZSByaWdodCBvZiBzdGVsbGFfYXBwOiBzdGVsbGFfYXBwIHdyaXRlcyA8YnI-IChjbGljaykgZmVlZGJhY2sgPGJyPiB0byBsb2NhbCBkYlxuICAgIHNpdGUgLT4-IHN0ZWxsYV9hcHA6IEdFVCBzZXNzaW9ucy88c2Vzc2lvbl9pZD4vZXhpdCBcbiAgICBOb3RlIHJpZ2h0IG9mIHN0ZWxsYV9hcHA6IE9wdGlvbmFsbHkgdGhlIDxicj4gc3RlbGxhX2FwcCBpcyBub3RpZmllZCA8YnI-IHdoZW4gc2Vzc2lvbnMgZW5kc1xuICAgIE5vdGUgcmlnaHQgb2Ygc3RlbGxhX2FwcDogc3RlbGxhX2FwcCBjaGVja3MgPGJyPiBsb2NhbCBkYiByZWd1bGFybHkgPGJyPiAoYnkgYSBnaXZlbiBpbnRlcnZhbCA8YnI-IGluIHRoZSBjb25maWctZmlsZSkgPGJyPiBhbmQgdXBsb2FkcyA8YnI-IGFsbCBlbmRlZCBzZXNzaW9ucyA8YnI-IHRvIHRoZSBzdGVsbGFfc2VydmVyXG5cbiIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2V9)

# To do

- [ ] sync experimental systems -> stella-server will write to config-file
- [ ] docker-container that wraps gesis-api
- [x] update expired token
- [x] check sessions that are not exited
- [x] simple interleaver
- [x] integrate api-endpoints into stella-app
- [x] endpoint "exit session"
- [x] endpoint "post feedback"
- [x] scheduler
- [x] scheduler: read local db
- [x] scheduler: write to stella-server
- [x] config-file  
        .credentials for stella-server (service)  
        .time interval of the scheduler  
        .address of the stella-server
- [x] user/session identification in stella-app (integrate possibility to send identifier)
- [x] Integrate Interleaving (cf. [LL4IR-API](https://bitbucket.org/living-labs/ll-api/src/master/))
- [ ] How to update the applications once they are deployed at the sites?
- [ ] output format of search script
- [ ] initial indexing of all containers, when starting the application
- [ ] DB/storage containing meta-info about docker-containers
- [ ] Webhook in repos of experimental systems: PING stella-server
- [x] [LL4IR-API](https://bitbucket.org/living-labs/ll-api/src/master/) + [OSIRRC jig](https://github.com/osirrc/jig) &rarr; best practices
- [x] Container-Interface (scheduled for 2019-11-28)
- [x] Large application project structure (Timo)
- [x] additional (prototypical) search engine, e.g. elasticsearch, and scheduling between search engines
- [x] Solr to external repository
- [x] implement easier logging (write logging file to host system)


## Prototype
This repository contains a first prototype of the STELLA application which will be deployed at the sites.
The API can be used to send a request to a (minimal) flask application. In return, the flask app will send back a
ranking which is retrieved from a container running Solr.

### Setup - Linux

1. Install [Docker](https://docs.docker.com/v17.12/install/)
2. Install [docker-compose](https://docs.docker.com/compose/install/)
3. [Add user to Docker group](https://docs.docker.com/install/linux/linux-postinstall/)
4. Make sure `docker.sock` is accessible (`/var/run/docker.sock` &rarr; `docker-compose.yml`)
5. Set path to sample data which will be indexed by Solr-container (&rarr; `docker-compose.yml`)
6. Copy some sample data to `~/data/sample`
7. Run `docker-compose up`. Depending on the size of the sample data collection, you have to wait before sending the first request to the API in order to retrieve results.

### Setup - MacOS

0. Install [Homebrew](https://brew.sh)
1. Install Docker:`brew cask install docker` 
2. Install Docker-compose:`brew cask install docker-compose` 
3. Copy some sample data to `~/data/sample`
4. Run `docker-compose up`. Depending on the size of the sample data collection, you have to wait before sending the first request to the API in order to retrieve results.

### Setup - Windows Desktop

1. Install [Docker](https://docs.docker.com/v17.12/install/)
   - Use Community edition (for free) and the latest stable version
   - When installing choose to use Windows containers instead if Linux containers
   - Enable Hyper-V and Container Features
      - To this end also enable Virtualization in your BIOS, if it is disabled
2. [docker-compose](https://docs.docker.com/compose/install/) is not needed in the Docker Desktop Version, as it is already installed; skip this step
3. No need to add user to [Docker group](https://docs.docker.com/install/linux/linux-postinstall/); skip this step
4. Make sure `docker.sock` is accessible (`/var/run/docker.sock` &rarr; `docker-compose.yml`); skip this step
5. Set path to sample data which will be indexed by Solr-container (&rarr; `docker-compose.yml`); based on the standard script in the stella-app the path to the data is $HOME\data\sample
7. Run `docker-compose up`. A s of now, using a CMD or Powershell (also Cygwin possible) go to stella app and run docker-compose with "docker-compose.exe up" (on windows). Depending on the size of the sample data collection, you have to wait before sending the first request to the API in order to retrieve results.
8. Typically, Docker needs access to the sample data --> share the drive the data with admin rights in the Docker settings under  "shared drives". 
    - If blocked by firewall, disable VPN
    - If still blocked by a firewall, check out https://success.docker.com/article/error-a-firewall-is-blocking-file-sharing-between-windows-and-the-containers
	
  
### Endpoints

- `GET /`: See a list of available containers that are running.

- `GET /stella/api/site/test/<string:container_name>`: Run test script in container whose name is specified by the endpoint (currently only `solr-container` is supported).

- `GET /stella/api/site/ranking/<string:query>`: Retrieve a ranking corresponding to the query specified at the endpoint. A JSON object with maximally 10 entries will be returned.
