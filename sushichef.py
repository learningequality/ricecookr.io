#!/usr/bin/env python
"""
Sikana's content is organized as follow:
- There is a top level set of categories (e.g. Health, Nature, Art, ...)
- Each category has programs (e.g. "Learn how to save a life", "Epidemics", ...)
- Each program has chapters
- Finally, each chapter has contents like videos, images, or PDF files.
"""
from bs4 import BeautifulSoup
import cgi
import json
import os
import requests
import yaml

from ricecooker.chefs import JsonTreeChef
from ricecooker.classes.licenses import get_license
from ricecooker.utils.jsontrees import read_tree_from_json, write_tree_to_json_tree
from le_utils.constants import licenses, languages, content_kinds, file_types

from sikana_api import SikanaApi


### Global variables
BASE_URL = "https://www.sikana.tv"
SIKANA_LANGUAGES = ["en", "fr", "es", "pt", "pt-br", "pl", "tr", "ru", "zh", "zh-tw", "ar"]
SIKANA_TRANSCRIPTS_DIR = 'chefdata/transcripts'


# Reading API credentials from parameters.yml
with open("credentials/parameters.yml", "r") as f:
    parameters = yaml.load(f)
SIKANA_CLIENT_ID = parameters["api"]["client_id"]
SIKANA_SECRET = parameters["api"]["secret"]


# DESCRIPTIONS
################################################################################

DEFAULT_CHANNEL_DESCRIPTIONS = {
    'ar': "في هذه القناة ستكتسب مهارات عملية لمساعدة نفسك والآخرين في مواقف الإسعافات الأولية والكوارث الطبيعية. الآلاف من المهارات في جيبك. حسّن من حياتك وحياة الآخرين في العالم من حولك من خلال التعلم العملي. انضم إلى مجتمعنا. وليكن لك تأثير"
}
def get_channel_description(language_code):
    if language_code in ['ar']:
        return DEFAULT_CHANNEL_DESCRIPTIONS[language_code]
    lang_url = 'https://www.sikana.tv/' + language_code
    html = requests.get(lang_url).text
    page = BeautifulSoup(html, 'html5lib')
    description_meta = page.find('head').find('meta', {'name':'description'})
    return description_meta['content']


# CORRECTIONS
################################################################################

CORRECTIONS_FILE = 'chefdata/corrections.json'
CORRECTIONS_DATA = json.load(open(CORRECTIONS_FILE))

def apply_corrections_to_json_tree(json_tree_path, corrections_for_source_id):
    channel_node = read_tree_from_json(json_tree_path)

    def _apply_corrections(subtree):
        source_id = subtree['source_id']
        if source_id in corrections_for_source_id:
            corrections = corrections_for_source_id[source_id]
            for attr, correction in corrections['attributes'].items():
                subtree[attr] = correction['new_value']
        # recusively continue down the tree
        if 'children' in subtree:
            for child in subtree['children']:
                _apply_corrections(child)

    _apply_corrections(channel_node)

    write_tree_to_json_tree(json_tree_path, channel_node)





# HELPER METHODS
################################################################################

def _getlang_caps(code):
    """
    Convert country code suffix to CAPITALS and match to internal represenation.
    """
    if '-' in code:
        parts = code.split('-')
        code = parts[0] + '-' + parts[1].upper()
    return languages.getlang(code)

def _get_video_transcript_url(language_code, video_id):
    """
    Returns the URL for getting video transcript.
    """
    url = BASE_URL + '/' + language_code
    url += '/download-transcription?videoId=' + str(video_id)
    url += '&lnCode=' + language_code
    return url

def _save_tanscript_content_to_filename(content, language_code, filename):
    # ensure dir
    transcript_dir = os.path.join(SIKANA_TRANSCRIPTS_DIR, language_code)
    if not os.path.exists(transcript_dir):
        os.makedirs(transcript_dir, exist_ok=True)
    # save
    if '/' in filename:
        filename = filename.replace('/', '_')
    transcript_path = os.path.join(transcript_dir, filename)
    with open(transcript_path, 'wb') as transcript_file:
        transcript_file.write(content)
    return transcript_path

    
def get_video_transcript(language_code, video):
    """
    Returns a dict(title=, path=) for the video transcript if it exists,
    else returns None.
    """
    transcript_url = _get_video_transcript_url(language_code, video['videoId'])
    response = requests.get(transcript_url)
    headers = response.headers
    if 'Content-Disposition' not in headers:
        return None  # Sikana `/download-transcription` will try to generate a
                     # transcript even for viewos that don't exist in language_code
                     # but we can distinguish these "best effort" transcriptions
                     # by the fact that response won' have a filename.
    else:
        content_disposition = headers['Content-Disposition']
        value, params = cgi.parse_header(content_disposition)
        if 'filename' in params:
            filename = params['filename'].encode('latin-1').decode('utf-8')
            title = filename.replace('.pdf', '')
        else:
            raise Exception("Content-Disposition present but no filename for url " + transcript_url)
        
        transcript_path = _save_tanscript_content_to_filename(response.content, language_code, filename)
        return { 'title':title, 'path':transcript_path, 'filename':filename, 'url':transcript_url }


def _remove_empty_topic_nodes(json_tree_path):
    channel_node = read_tree_from_json(json_tree_path)

    def _remove_empty_child_topic_nodes(subtree):
        if 'children' in subtree:
            new_children = []
            for child in subtree['children']:
                if 'children' in child:
                    # recursive pre-traversal down the tree...
                    _remove_empty_child_topic_nodes(child)
                    if len(child['children']) == 0:
                        pass                        # skip empty topic nodes 
                    else:
                        new_children.append(child)  # keep non-empty topic nodes
                else:
                    new_children.append(child)      # keep leaf nodes
            subtree['children'] = new_children
    _remove_empty_child_topic_nodes(channel_node)

    write_tree_to_json_tree(json_tree_path, channel_node)





# MAIN TREE-BUILDING LOGIC
################################################################################


def _build_tree(channel_node, language_code):
    """
    Builds the content tree with Sikana content using Sikana API.
    """
    print("Started building the content structure from Sikana API.")
    lang_obj = _getlang_caps(language_code)

    # Building an access to Sikana API
    sikana_api = SikanaApi(
        SIKANA_CLIENT_ID,
        SIKANA_SECRET
    )

    # Taking categories from Sikana API
    categories = sikana_api.get_categories(language_code)

    # Adding categories to tree
    for key, cat in categories["categories"].items():

        # 21 July 2020: refresh access token after each category to avoid the
        # error HTTP 401 that says "The access token provided has expired."
        sikana_api.token = sikana_api.get_access_token(sikana_api.client_id, sikana_api.secret)


        print("#### CATEGORY: {}".format(cat["name"]))
        category_node = dict(                                    # category node
            kind=content_kinds.TOPIC,
            source_id = cat["name"],
            title = cat["localizedName"],
            children=[],
        )
        channel_node['children'].append(category_node)

        # Getting programs belonging to this category from Sikana API
        programs = sikana_api.get_programs(language_code, cat["name"])

        for prog in programs:
            print("### PROGRAM: {}".format(programs[prog]["name"]))
            program_node = dict(                                  # program node
                kind=content_kinds.TOPIC,
                source_id = programs[prog]["nameCanonical"],
                title = programs[prog]["name"],
                description = programs[prog].get("description"),
                thumbnail = programs[prog].get("image"),
                language = lang_obj.code,
                children=[],
            )
            category_node['children'].append(program_node)

            # Getting program details from Sikana API
            program = sikana_api.get_program(language_code, programs[prog]["nameCanonical"])

            for chap in program["listChaptersVideos"]:
                print("## CHAPTER: {}. {}".format(program["listChaptersVideos"][chap]["infos"]["id"], program["listChaptersVideos"][chap]["infos"]["name"]))
                chapter_node = dict(                              # chapter node
                    kind=content_kinds.TOPIC,
                    source_id = str(program["listChaptersVideos"][chap]["infos"]["id"]),
                    title = program["listChaptersVideos"][chap]["infos"]["name"],
                    children=[],
                )
                program_node['children'].append(chapter_node)

                # For each video in this chapter
                if "videos" in program["listChaptersVideos"][chap]:
                    for v in program["listChaptersVideos"][chap]["videos"]:
                        # Getting video details from Sikana API
                        video = sikana_api.get_video(language_code, v['nameCanonical'])

                        print("# VIDEO: {}".format(video["video"]["title"]))

                        # If no description, we use an empty string
                        try:
                            description = video["video"]["description"]
                        except KeyError:
                            description = ""
                        
                        if 'youtube_id' not in video["video"]:
                            print("# SKIPPING video because MISSING youtube_id in video json: {}".format(video["video"]))
                            continue

                        # Video node
                        video_node = dict(
                            kind=content_kinds.VIDEO,
                            source_id = v["nameCanonical"],
                            title = video["video"]["title"],
                            description = description,
                            derive_thumbnail = False,   # video-specific data
                            license = get_license(licenses.CC_BY_NC_ND, copyright_holder="Sikana Education").as_dict(),
                            thumbnail = "https://img.youtube.com/vi/{}/maxresdefault.jpg".format(video["video"]["youtube_id"]),
                            language = lang_obj.code,
                            files=[],
                        )
                        video_file = dict(
                            file_type=file_types.VIDEO,
                            youtube_id=video["video"]["youtube_id"],
                            high_resolution = False,  # get 480v instead of 720v
                            download_settings = {
                                'postprocessors': [{
                                    'key': 'ExecAfterDownload',
                                    'exec_cmd': 'echo "Compressing to CRF 28" && ffmpeg -i {} -crf 28 {}_tmp.mp4 && mv {}_tmp.mp4 {}',
                                }]
                            }
                        )
                        video_node['files'].append(video_file)
                        # For each subtitle of this video
                        for sub in video["subtitles"]:
                            sikana_sub_code = video["subtitles"][sub]["code"]
                            sub_lang_obj = _getlang_caps(sikana_sub_code)
                            print("#    SUBS: {}".format(sub_lang_obj.code))
                            sub_file = dict(
                                file_type = file_types.SUBTITLES,
                                path = BASE_URL + video["subtitles"][sub]["fileUrl"],
                                language = sub_lang_obj.code,
                            )
                            video_node['files'].append(sub_file)
                        chapter_node['children'].append(video_node)

                        # New Oct 2018: add PDF doc of transcript for each video
                        transcript = get_video_transcript(language_code, video)
                        if transcript:
                            print("#    TRANSCRIPT: {} from {}".format(transcript['title'], transcript['url']))
                            # Transcript document node
                            transcript_node = dict(
                                kind=content_kinds.DOCUMENT,
                                source_id = transcript['url'],
                                title = transcript['title'],
                                description = description,
                                license = get_license(licenses.CC_BY_NC_ND, copyright_holder="Sikana Education").as_dict(),
                                language = lang_obj.code,
                                files=[],
                            )
                            transcript_file = dict(
                                file_type=file_types.DOCUMENT,
                                path=transcript['path']
                            )
                            transcript_node['files'].append(transcript_file)
                            chapter_node['children'].append(transcript_node)




# CHEF
################################################################################

class SikanaChef(JsonTreeChef):
    """
    This class contains the `get_channel` and `construct_channel` methods needed
    to build the Sikana channels on Koibri Studio.
    """
    RICECOOKER_JSON_TREE_TPL = 'ricecooker_json_tree_{}.json'

    def get_json_tree_path(self, *args, **kwargs):
        """
        Return path to ricecooker json tree file. Override this method to use
        a custom filename, e.g., for channel with multiple languages.
        """
        # Channel language
        if "language_code" in kwargs:
            language_code = kwargs["language_code"]
        else:
            raise Exception('No language_code option passed in --- specify language e.g. language_code=ar')
        lang_obj = _getlang_caps(language_code)
        json_filename = self.RICECOOKER_JSON_TREE_TPL.format(lang_obj.code)
        json_tree_path = os.path.join(self.TREES_DATA_DIR, json_filename)
        return json_tree_path

    def pre_run(self, args, options):
        """
        Build the ricecooker json tree. Uses `language_code` from `kwargs`.
        """
        # Channel language
        if "language_code" in options:
            language_code = options["language_code"]
        else:
            raise Exception('No language_code option passed in --- specify language e.g. language_code=ar')
        lang_obj = _getlang_caps(language_code)

        channel_description = get_channel_description(language_code)

        channel_node = dict(
            source_domain = "sikana.tv",
            source_id = "sikana-channel-" + language_code,
            title = "Sikana (" + lang_obj.first_native_name + ")",
            description = channel_description,
            thumbnail = "./sikana_logo.png",
            language=lang_obj.code,
            children=[],
        )
        _build_tree(channel_node, language_code)   # Fill the channel with Sikana content

        kwargs = {}   # combined dictionary of argparse args and extra options
        kwargs.update(args)
        kwargs.update(options)
        json_tree_path = self.get_json_tree_path(**kwargs)

        print('Writing ricecooker json tree to ', json_tree_path)
        write_tree_to_json_tree(json_tree_path, channel_node)
        _remove_empty_topic_nodes(json_tree_path)
        if language_code == 'ar':
            corrections_for_source_id = CORRECTIONS_DATA['ar']['correction_for_source_id']
            apply_corrections_to_json_tree(json_tree_path, corrections_for_source_id)



# CLI
################################################################################

if __name__ == '__main__':
    sikana_chef = SikanaChef()
    sikana_chef.main()
