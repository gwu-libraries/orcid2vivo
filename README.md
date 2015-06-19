# orcid2vivo
Proof of concept code for retrieving data from the ORCID API and crosswalking to VIVO-ISF.

[![Build status](https://travis-ci.org/gwu-libraries/orcid2vivo.svg)]

Try it at  http://gw-orcid2vivo.wrlc.org/orcid2vivo

## Commandline
* Supports outputting to:
    * screen / stdout
    * file
    * load to VIVO instance (via SPARQL Update)
* Supports multiple RDF serializations.
* Allows specifying:
    * VIVO namespace
    * An id or URI for the person.
    * Class for the person.

```
(ENV)GLSS-F0G5RP:orcid2vivo justinlittman$ python orcid2vivo.py -h
usage: orcid2vivo.py [-h] [--format {xml,n3,turtle,nt,pretty-xml,trix}]
                     [--file FILE] [--endpoint ENDPOINT] [--username USERNAME]
                     [--password PASSWORD] [--person-id PERSON_ID]
                     [--person-uri PERSON_URI] [--namespace NAMESPACE]
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
  --person-uri PERSON_URI
                        A URI for the person. If not provided, one will be
                        created from the orcid id or person id.
  --namespace NAMESPACE
                        VIVO namespace. Default is
                        http://vivo.mydomain.edu/individual/.
  --person-class {FacultyMember,FacultyMemberEmeritus,Librarian,LibrarianEmeritus,NonAcademic,NonFacultyAcademic,ProfessorEmeritus,Student}
                        Class (in VIVO Core ontology) for a person. Default is
                        a FOAF Person.
  --skip-person         Skip adding triples declaring the person and the
                        person's name.

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
    * An id or URI for the person.
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

##Tests

```
GLSS-F0G5RP:orcid2vivo justinlittman$ python -m unittest discover
```

##Strategies for generating URIs and/or creating entities
Approaches to generating URIs and creating entities (e.g., journals or co-authors) are abstracted into strategies.  Default strategies are provided, but they can be replaced with other strategies is necessary to meet local requirements.

The strategy for generating URIs is provided by a class that has the following method:

```
    def to_uri(self, clazz, attrs, general_clazz=None):
        """
        Given an RDF class and a set of attributes for an entity, produce a URI.
        :param clazz: the class of the entity.
        :param attrs: a map of identifying attributes for an entity.
        :param general_clazz: a superclass of the entity that can be used to group like entities.
        :return: URI for the entity.
        """
```

The strategy for creating entities is provided by a class that has the following method:

```
    def should_create(self, clazz, uri):
        """
        Determine whether an entity should be created.
        :param clazz: Class of the entity.
        :param uri: URI of the entity.
        :return: True if the entity should be created.
        """
```

It may be desirable to skip creating entities if those entities already exist in the triple store.  For example, this shows the triples when the journal is created:

```
d:academicarticle-df4d61373e64c72681d74829ea92071a vivo:hasPublicationVenue d:journal-65a2d6d4d80fdbbd78268bf4e814ee01 ;

d:journal-65a2d6d4d80fdbbd78268bf4e814ee01 a bibo:Journal ;
    rdfs:label "D-Lib Magazine" ;
    bibo:issn "1082-9873" .
```

and this shows the triples when it is not created:

```
d:academicarticle-df4d61373e64c72681d74829ea92071a vivo:hasPublicationVenue d:journal-65a2d6d4d80fdbbd78268bf4e814ee01 ;

```

Depending on the strategies to be implemented, it may be a useful approach to combine both strategies into a single class.

##Caveats:
* All data is not cross walked to VIVO-ISF.
* Password for SPARQL Update is not handled securely.

##Other:
* Feedback / tickets / pull requests welcome.
* Consider using with [vivo-docker](https://github.com/gwu-libraries/vivo-docker) to put together an environment for experimenting with crosswalking ORCID to VIVO. 