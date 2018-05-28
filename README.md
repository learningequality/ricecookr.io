# ricecookr.io
Integration of Sikana's content into Learning Equality's [Kolibri Studio](https://studio.learningequality.org/).

Uses [Ricecooker](https://github.com/learningequality/ricecooker) framework.


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

### How to use it
Each time you want to use the script, you have to ensure the `virtualenv` you
previously created is activated (it appears in your prompt).
If not, run the command `source venv/bin/activate`.

Run the following command to build a channel for the language of your choice:

    ./sushichef.py -v --reset --token=<YOUR_TOKEN_HERE> language_code=<LANGUAGE_CODE_HERE>


### Production setup

Currently setup on `vader` under the `/data/sushi-chef-sikana` folder.
Scheduled to run on the third day of every month.