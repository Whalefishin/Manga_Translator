import argostranslate.package
import argostranslate.translate

# from_code = 'en'
# to_code = 'ja'

from_code = 'ja'
to_code = 'en'

# # Download and install Argos Translate package
# argostranslate.package.update_package_index()
# available_packages = argostranslate.package.get_available_packages()
# # print ([x.to_code for x in available_packages])
# package_to_install = next(
#     filter(
#         lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
#     )
# )
# argostranslate.package.install_from_path(package_to_install.download())

# Translate
# translatedText = argostranslate.translate.translate("Hello World", from_code, to_code)
available_packages = argostranslate.package.get_available_packages()
print ([(x.from_code, x.to_code) for x in available_packages])
translatedText = argostranslate.translate.translate("ハローワールド", from_code, to_code)
print(translatedText)
# '¡Hola Mundo!'