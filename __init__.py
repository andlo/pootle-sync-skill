import zipfile
import wget
import polib
import os 
from os import walk, makedirs
from os.path import join, basename, exists, expanduser, isdir, isfile
from mycroft import MycroftSkill, intent_file_handler


class PootleSync(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        translations_dir = self.config_core.get('skills').get('translations_dir')
        translations_dir = expanduser(translations_dir)
        user_lang_path = self.settings.get('lang_path') 
        if user_lang_path:
            self.lang_path = user_lang_path
        if (translations_dir):
            self.lang_path = translations_dir
        else:
            self.lang_path = join(self.file_system.path, "translations")

        self.log.info("Translations are saved in " + self.lang_path)

#        if self.settings.get('synctimer', 1) >= 1:
#            sync = self.settings.get('synctimer', 1) * 3600
#            self.schedule_repeating_event(self.sync_pootle, None, sync,
#                                          name='sync_pootle')
#            self.log.info("start pootdle event every " + str(self.settings.get('synctimer')) + " h")

    @intent_file_handler('sync.pootle.intent')
    def handle_sync_pootle(self, message):
        self.speak_dialog('sync.pootle')
        self.sync_pootle()

    def sync_pootle(self):
        if self.settings.get('synctimer', 1) < 1:
            self.cancel_scheduled_event('sync_pootle')
        self.poodle_downloader()
        folder = self.file_system.path+"/da/da/mycroft-skills"
        self.find_po(folder)
        #self.log.info(translation)

    def find_po(self, folder):
        for root, dirs, files in os.walk(folder):
            for f in files:
                filename = join(root, f)
                if filename.endswith('.po'):
                    output = self.parse_po_file(filename)
                    filename = filename.replace(folder + "/", '')
                    skillname = filename[:-6]
                    for data in output:
                        self.log.info(self.lang_path + ' ' + skillname + ' ' +  self.lang + ' ' + data)
                        filename = join(self.lang_path, skillname, self.lang, data)
                        self.writing_sentence(output[data], data, filename)

    def poodle_downloader(self):
        self.log.info("start download")
        if os.path.isfile(self.file_system.path+"/"+self.lang[:-3]+".zip"):
            os.remove(self.file_system.path+"/"+self.lang[:-3]+".zip")
        wget.download("https://translate.mycroft.ai/export/?path=/"+self.lang[:-3], self.file_system.path+"/"+self.lang[:-3]+".zip")
        with zipfile.ZipFile(self.file_system.path+"/"+self.lang[:-3]+".zip",'r') as zfile:
                zfile.extractall(self.file_system.path)
        self.speak_dialog('sync.pootle')

    def reading_sentence(self, data, filename):
        sentence = []
        fobj_in = open(filename, "r")
        for line in fobj_in:
            sentence = sentence.append(line)
        fobj_in.close()
        return sentence

    def writing_sentence(self, sentence, data, filename):
        sentence = "\n".join(sentence)
        folder = filename.replace(data, '')
        if not os.path.isdir(folder):
            os.makedirs(folder)
        fobj_out = open(filename, "w")
        self.log.info("write file: "+str(filename))
        fobj_out.write(str(sentence) + "\n")
        fobj_out.close()

    def parse_po_file(self, path):
        """ Create dictionary with translated files as key containing
        the file content as a list.

        Arguments:
            path: path to the po-file of the translation

        Returns:
            Dictionary mapping files to translated content
        """
        out_files = {}  # Dict with all the files of the skill
        # Load the .po file
        po = polib.pofile(path)

        for entity in po:
            for out_file, _ in entity.occurrences:
                f = out_file.split('/')[-1] # Get only the filename
                content = out_files.get(f, [])
                content.append(entity.msgstr)
                out_files[f] = content
        self.log.info(out_files)
        return out_files

    def shutdown(self):
        self.cancel_scheduled_event('sync_pootle')
        super(PootleSync, self).shutdown()


def create_skill():
    return PootleSync()