# ricecookr.io
Integration of Sikana's content into Learning Equality's [Kolibri Studio](https://studio.learningequality.org/).

Uses [Ricecooker](https://github.com/learningequality/ricecooker) framework.


## TODO
  - drop empty category/program/chapter folders (no need to show Topics if no videos in them)
    e.g. Arabic has only Health CATEGORY https://studio.learningequality.org/channels/09d96cfabec451309066517930bdab9f/edit/09d96cf


### Sikana's data structure
For each language, you'll find the content organized as follow:

```
Category
`-- Program
    `-- Chapter
        `-- Video
```

This script intends to create a Sikana channel per language ("Sikana EN", "Sikana FR", ...)


### Installation instructions
For this, you will need to have `python3` and [`virtualenv`](https://virtualenv.pypa.io/en/stable/)
installed on your machine (please read the manual to understand basically how it works).

In the directory containing the code, run following commands:
  - `virtualenv -p python3 venv`
  - `source venv/bin/activate`
  - `pip3 install -r requirements.txt`
  - Then, copy-paste `credentials/parameters.yml.dist` to `credentials/parameters.yml`
    and fill it with your credentials to Sikana's API and Kolibri token.

### Running the chefs
Each time you want to use the script, you have to ensure the `virtualenv` you
previously created is activated (it appears in your prompt).
If not, run the command `source venv/bin/activate`.

Run the following command to build a channel for the language of your choice:

    ./sushichef.py -v --reset --token=<YOUR_TOKEN_HERE> language_code=<LANGUAGE_CODE_HERE>

To run all the chef for all languages, you can add your Studio token to the file
`credentials/parameters.yml` then run the following single-line command:

    nohup ./uploadchannels.py &

Note: this will likely take a whole day for the first time.


### Production setup

Currently setup on `vader` under the `/data/sushi-chef-sikana` folder.
TODO: scheduled to run on the third day of every month.

    
