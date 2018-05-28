#!/usr/bin/env python
"""
Sikana's content is organized as follow:
- There is a top level set of categories (e.g. Health, Nature, Art, ...)
- Each category has programs (e.g. "Learn how to save a life", "Epidemics", ...)
- Each program has chapters
- Finally, each chapter has contents like videos, images, or PDF files.
"""
import yaml
from ricecooker.chefs import SushiChef
from ricecooker.classes import nodes, files
from ricecooker.classes.nodes import ChannelNode
from ricecooker.classes.licenses import get_license
from ricecooker.exceptions import raise_for_invalid_channel

from le_utils.constants import licenses, languages
from sikana_api import SikanaApi


### Global variables
BASE_URL = "https://www.sikana.tv"
SIKANA_LANGUAGES = ["en", "fr", "es", "pt", "pt-br", "pl", "tr", "ru", "zh", "zh-tw", "ar"]

# Reading API credentials from parameters.yml
with open("credentials/parameters.yml", "r") as f:
    parameters = yaml.load(f)
SIKANA_CLIENT_ID = parameters["api"]["client_id"]
SIKANA_SECRET = parameters["api"]["secret"]



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



# MAIN TREE-BUILDING LOGIC
################################################################################

def _build_tree(channel_node, language_code):
    """
    Builds the content tree with Sikana content
    using Sikana API
    """
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
        print("#### CATEGORY: {}".format(cat["name"]))
        category_node = nodes.TopicNode( # category node
            source_id = cat["name"],
            title = cat["localizedName"]
        )
        channel_node.add_child(category_node)

        # Getting programs belonging to this category from Sikana API
        programs = sikana_api.get_programs(language_code, cat["name"])

        for prog in programs:
            print("### PROGRAM: {}".format(programs[prog]["name"]))
            program_node = nodes.TopicNode( # program node
                source_id = programs[prog]["nameCanonical"],
                title = programs[prog]["name"],
                description = programs[prog].get("description"),
                thumbnail = programs[prog].get("image"),
                language = lang_obj.code,
            )
            category_node.add_child(program_node)

            # Getting program details from Sikana API
            program = sikana_api.get_program(language_code, programs[prog]["nameCanonical"])

            for chap in program["listChaptersVideos"]:
                print("## CHAPTER: {}. {}".format(program["listChaptersVideos"][chap]["infos"]["id"], program["listChaptersVideos"][chap]["infos"]["name"]))
                chapter_node = nodes.TopicNode( # chapter node
                    source_id = str(program["listChaptersVideos"][chap]["infos"]["id"]),
                    title = program["listChaptersVideos"][chap]["infos"]["name"],
                )
                program_node.add_child(chapter_node)

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

                        video_node = nodes.VideoNode(
                            source_id = v["nameCanonical"],
                            title = video["video"]["title"],
                            description = description,
                            derive_thumbnail = False,   # video-specific data
                            license = get_license(licenses.CC_BY_NC_ND, copyright_holder="Sikana Education"),
                            thumbnail = "https://img.youtube.com/vi/{}/maxresdefault.jpg".format(video["video"]["youtube_id"]),
                            language = lang_obj.code,
                        )
                        video_file = files.YouTubeVideoFile(
                            youtube_id=video["video"]["youtube_id"],
                            high_resolution = False,  # get 480v instead of 720v
                        )
                        video_node.add_file(video_file)
                        chapter_node.add_child(video_node)

                        # For each subtitle of this video
                        for sub in video["subtitles"]:
                            sikana_sub_code = video["subtitles"][sub]["code"]
                            sub_lang_obj = _getlang_caps(sikana_sub_code)
                            sub_file = files.SubtitleFile(
                                path = BASE_URL + video["subtitles"][sub]["fileUrl"],
                                language = sub_lang_obj.code,
                            )
                            video_node.add_file(sub_file)

    return channel_node



# CHEF
################################################################################

class SikanaChef(SushiChef):
    """
    This class contains the `get_channel` and `construct_channel` methods needed
    to build the Sikana channels on Koibri Studio.
    """

    def get_channel(self, **kwargs):
        """
        Build the `ChannelNode` object. Uses `language_code` from `kwargs`.
        """
        # Channel language
        if "language_code" in kwargs:
            language_code = kwargs["language_code"]
        else:
            language_code = "en"  # default to en if no language specified on command line

        lang_obj = _getlang_caps(language_code)
        channel = ChannelNode(
            source_domain = "sikana.tv",
            source_id = "sikana-channel-" + language_code,
            title = "Sikana (" + lang_obj.first_native_name + ")",
            description = "Sikana videos are tiny nuggets of practical knowledge and life skills. "
                          "Topics include sports, cooking, arts, health, agriculture, and much more. "
                          "The videos are fun to watch and provide useful non-academic learning.",
            thumbnail = "./sikana_logo.png",
            language=lang_obj.code,
        )

        return channel


    def construct_channel(self, **kwargs):
        """
        Constructs the Kolibri channel for the language `language_code`.
        """

        # Channel language
        if "language_code" in kwargs:
            language_code = kwargs["language_code"]
        else:
            language_code = "en"

        channel = self.get_channel(**kwargs)  # Get the channel object
        _build_tree(channel, language_code)   # Fill the channel with Sikana content
        raise_for_invalid_channel(channel)    # Raise exceptions

        return channel



# CLI
################################################################################

if __name__ == '__main__':
    sikana_chef = SikanaChef()
    sikana_chef.main()
