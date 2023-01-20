import os
from tqdm import tqdm
# from google_trans_new import google_translator  
# translator = google_translator()  
import pickle
import subprocess
import argostranslate.translate
import argostranslate.package
import json
from google.cloud import translate
import html

# =================================================================================== #
#                           For Google Translation API                                #
# =================================================================================== #
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"cred/translation_sa_key.json"
project_id = json.load(open('cred/translation_project_settings.json'))['id']



class TextTranslator():
    def __init__(self, args, translatorType, ocr_folder):
        self.translatorType = translatorType
        self.args = args
        self.get_lang_codes()
        self.ocr_folder = ocr_folder # debugging outputs are saved here
        self.do_additional_setup()

    def do_additional_setup(self):
        """Do some additional setup particular to each translation engine.
        """
        if self.args.translator == 'google':
            # used for google cloud API
            self.google_api_parent = f"projects/{project_id}"
            self.google_api_client = translate.TranslationServiceClient()
        elif self.args.translator == 'argos':
            if self.args.target_lang != 'chinese_simplified':
                # install the necessary language packages
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()
                # print ([x.to_code for x in available_packages])
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == self.source_code and x.to_code == self.target_code, available_packages
                    )
                )
                argostranslate.package.install_from_path(package_to_install.download())
            else:
                # install language packages if needed
                # need to install jp -> en, en -> zh
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()
                # print ([x.to_code for x in available_packages])
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == self.source_code and x.to_code == 'en', available_packages
                    )
                )
                argostranslate.package.install_from_path(package_to_install.download())
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == 'en' and x.to_code == self.target_code, available_packages
                    )
                )
                argostranslate.package.install_from_path(package_to_install.download())

    def get_lang_codes(self):
        """Map the input and output language name to their respective codes
        """
        code_dict = {}
        code_dict['japanese'] = 'ja'
        code_dict['english'] = 'en'
        if self.args.translator == 'argos':
            code_dict['chinese_simplified'] = 'zh'
        elif self.args.translator == 'google':
            code_dict['chinese_simplified'] = 'zh-CN'
        self.source_code = code_dict[self.args.source_lang]
        self.target_code = code_dict[self.args.target_lang]

    def translateGoogle(self, text):
        """Call Google API to translated the input text

        Args:
            text(str): text to translate

        Returns:
            translated text
        """
        response = self.google_api_client.translate_text(
            contents = text,
            target_language_code = self.target_code,
            parent = self.google_api_parent,
        )

        # decode with html to deal with special chars, e.g., can&#39;t -> can't
        # TODO: check if this works with Chinese
        return [html.unescape(translation.translated_text) for translation in response.translations]

    def translateArgos(self, text):
        """Translate the input text with argos-translate

        Args:
            text (str): text to translate

        Returns:
            translated text
        """
        if self.args.target_lang == 'chinese_simplified':
            # argos doesn't support direct translation from japanese to chinese
            # so we have to do japanese -> english -> chinese
            text_en = argostranslate.translate.translate(text, self.source_code, 'en')
            return argostranslate.translate.translate(text_en, 'en', self.target_code)
        else:
            return argostranslate.translate.translate(text, self.source_code, self.target_code)
      
    def translate(self, textList):
        """Translate the given list of text with the specified framework

        Args:
            textList (list): texts to translate

        Returns:
            translated texts
        """
        if self.translatorType == "google": # google can do batch translation
            textList_trans = self.translateGoogle(textList)
        else:
            if self.translatorType == "argos":
                transFunc=self.translateArgos
            else:
                raise NotImplementedError()
                
            textList_trans = self.translateList(textList, transFunc)

        if self.args.verbose: # debugging outputs
            # save translated texts
            log_dir = os.path.join(self.ocr_folder, 'translated_texts.txt')
            with open(log_dir, 'a', encoding='utf8') as f:
                for i, line in enumerate(textList_trans):
                    f.write('text {} translates to: {} \n'.format(i, line))

        return textList_trans
        
    def translateList(self, textList, translateFunc):
        """A subroutine of translate(). Translate a list of text one by one with the designated function.

        Args:
            textList (list): list of texts
            translateFunc (function): translation function

        Returns:
            textList_trans: list of translated texts
        """
        textList_trans = []
        for text in textList:
            text_trans = translateFunc(text) if len(text) != 0 else ""
            textList_trans += [text_trans] 

        return textList_trans


if __name__ == "__main__":
    pass