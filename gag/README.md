
# GAG Web Frontend
* Folder: gag

### Download the cobra egg files
* Put these into the `cobra_eggs` folder

`wget "https://207.162.210.84/cobra/_downloads/acicobra-4.0_1h-py2.7.egg" --no-check-certificate`

`wget "https://207.162.210.84/cobra/_downloads/acimodel-4.0_1h-py2.7.egg" --no-check-certificate`

### Build
`docker build -t gag:latest .`

### Prod Run
`docker run -p 80:80 -d gag`

### Dev Run
* **Change to your local folder if wanted**
* ``` LOCAL=`pwd` ```
* `docker run -v $LOCAL:/usr/local/gag -p 80:80 -d gag:latest`

### Dev Bash
* **Use for debugging - lots of info on the screen when you run it local**

* ``` LOCAL=`pwd` ```
* `docker run -v $LOCAL:/usr/local/gag -p 80:80 -ti gag:latest bash`

