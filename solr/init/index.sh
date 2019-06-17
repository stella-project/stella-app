#!/bin/bash
#echo "Hello world! (sent from solr container)"

solr start -p 8983
solr create_core -c collection -p 8983
post -c collection -p 8983 /opt/solr/collection/
solr stop -p 8983
