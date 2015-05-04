# orcid2vivo
Proof of concept code for retrieving data from the ORCID API and crosswalking to VIVO-ISF.

Try it at  http://gw-orcid2vivo.wrlc.org/orcid2vivo

## Commandline
* Supports outputting to:
    * screen / stdout
    * file
    * load to VIVO instance (via SPARQL Update)
* Supports multiple RDF serializations.
* Allows specifying:
    * VIVO namespace
    * An id for the person.
    * Class for the person.

    
```

(ENV)GLSS-F0G5RP:orcid2vivo justinlittman$ python orcid2vivo.py -h
usage: orcid2vivo.py [-h] [--format {xml,n3,turtle,nt,pretty-xml,trix}]
                     [--file FILE] [--endpoint ENDPOINT] [--username USERNAME]
                     [--password PASSWORD] [--person-id PERSON_ID]
                     [--namespace NAMESPACE]
                     [--person-class {FacultyMember,FacultyMemberEmeritus,Librarian,LibrarianEmeritus,NonAcademic,NonFacultyAcademic,ProfessorEmeritus,Student}]
                     [--skip-person]
                     orcid_id

positional arguments:
  orcid_id

optional arguments:
  -h, --help            show this help message and exit
  --format {xml,n3,turtle,nt,pretty-xml,trix}
                        The RDF format for serializing. Default is turtle.
  --file FILE           Filepath to which to serialize.
  --endpoint ENDPOINT   Endpoint for SPARQL Update of VIVO instance,e.g.,
                        http://localhost/vivo/api/sparqlUpdate. Also provide
                        --username and --password.
  --username USERNAME   Username for VIVO root.
  --password PASSWORD   Password for VIVO root.
  --person-id PERSON_ID
                        Id for the person to use when constructing the
                        person's URI. If not provided, the orcid id will be
                        used.
  --namespace NAMESPACE
                        VIVO namespace. Default is
                        http://vivo.mydomain.edu/individual/.
  --person-class {FacultyMember,FacultyMemberEmeritus,Librarian,LibrarianEmeritus,NonAcademic,NonFacultyAcademic,ProfessorEmeritus,Student}
                        Class (in VIVO Core ontology) for a person. Default is
                        a FOAF Person.
  --skip-person         Skip adding triples declaring the person and the
                        person's name
                        
```

For example:
```
(ENV)GLSS-F0G5RP:orcid2vivo justinlittman$ python orcid2vivo.py 0000-0003-1527-0030
```

## Web application
* Supports outputting to:
    * web page
    * download
    * load to VIVO instance (via SPARQL Update)
* Also supports outputting of ORCID profile to web page.
* Can be invoked from web form and http client. 
* Supports multiple RDF serializations.
* Allows specifying:
    * VIVO namespace
    * An id for the person.
    * Class for the person.
* Allows providing various default values when starting the application.

```

(ENV)GLSS-F0G5RP:orcid2vivo justinlittman$ python orcid2vivo_service.py -h
usage: orcid2vivo_service.py [-h]
                             [--format {xml,n3,turtle,nt,pretty-xml,trix}]
                             [--endpoint ENDPOINT] [--username USERNAME]
                             [--password PASSWORD] [--namespace NAMESPACE]
                             [--person-class {FacultyMember,FacultyMemberEmeritus,Librarian,LibrarianEmeritus,NonAcademic,NonFacultyAcademic,ProfessorEmeritus,Student}]
                             [--skip-person] [--debug] [--port PORT]

optional arguments:
  -h, --help            show this help message and exit
  --format {xml,n3,turtle,nt,pretty-xml,trix}
                        The RDF format for serializing. Default is turtle.
  --endpoint ENDPOINT   Endpoint for SPARQL Update of VIVO instance,e.g.,
                        http://localhost/vivo/api/sparqlUpdate.
  --username USERNAME   Username for VIVO root.
  --password PASSWORD   Password for VIVO root.
  --namespace NAMESPACE
                        VIVO namespace. Default is
                        http://vivo.mydomain.edu/individual/.
  --person-class {FacultyMember,FacultyMemberEmeritus,Librarian,LibrarianEmeritus,NonAcademic,NonFacultyAcademic,ProfessorEmeritus,Student}
                        Class (in VIVO Core ontology) for a person. Default is
                        a FOAF Person.
  --skip-person         Skip adding triples declaring the person and the
                        person's name.
  --debug
  --port PORT           The port the service should run on. Default is 5000.

```

For example, to start:
```
(ENV)GLSS-F0G5RP:orcid2vivo justinlittman$ python orcid2vivo_service.py
```

The web form will now be available at http://localhost:5000/.

### Invoke using curl

```
GLSS-F0G5RP:orcid2vivo justinlittman$ curl --data "orcid_id=0000-0003-1527-0030&format=turtle" http://localhost:5000/
```

### Docker

The web application can be deployed to a [Docker](https://www.docker.com/) container.

```
GLSS-F0G5RP:orcid2vivo justinlittman$ docker build -t orcid2vivo .
GLSS-F0G5RP:orcid2vivo justinlittman$ docker run -e "O2V_ENDPOINT=http://vivo:8080/vivo/api/sparqlUpdate" -e "O2V_USERNAME=vivo_root@mydomain.edu" -e "O2V_PASSWORD=password" -e "O2V_NAMESPACE=http://vivo.mydomain.edu/" -p "5000:5000" -d orcid2vivo
```

The web form will now be available at http://localhost:5000/.  (Note:  If using boot2docker, use result of `boot2docker ip` instead of localhost.)


##Caveats:
* All data is not cross walked to VIVO-ISF.
* Not ready for production use.
* Password for SPARQL Update is not handled securely.

##Other:
* Feedback / tickets / pull requests welcome.
* Consider using with [vivo-docker](https://github.com/gwu-libraries/vivo-docker) to put together an environment for experimenting with crosswalking ORCID to VIVO. 