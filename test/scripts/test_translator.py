from transformers import MarianMTModel, MarianTokenizer
from typing import Sequence

class Translator:
    def __init__(self, source_lang: str, dest_lang: str) -> None:
        self.model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{dest_lang}'
        self.model = MarianMTModel.from_pretrained(self.model_name)
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        
    def translate(self, texts: Sequence[str]) -> Sequence[str]:
        tokens = self.tokenizer(list(texts), return_tensors="pt", padding=True)
        translate_tokens = self.model.generate(**tokens)
        return [self.tokenizer.decode(t, skip_special_tokens=True) for t in translate_tokens]
        
        
# marian_ru_en = Translator('ru', 'en')
# result = marian_ru_en.translate(['что слишком сознавать — это болезнь, настоящая, полная болезнь.'])
# print (result)
# # Returns: ['That being too conscious is a disease, a real, complete disease.']

marian_ru_en = Translator('ja', 'en')
result = marian_ru_en.translate(['僕は下僕を雇う主人として力を見せてやったんだ！'])
print (result)