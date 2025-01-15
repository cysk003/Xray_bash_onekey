import re
import time
import json
import os
from googletrans import Translator, LANGUAGES

def load_translation_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_translation_cache(cache_file, translations):
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)

def translate_po_file(input_file, output_file, target_lang):
    cache_file = f'po/cache_{target_lang}.json'
    translations = load_translation_cache(cache_file)
    
    # 使用最新的 Translator，并设置更可靠的服务 URL
    translator = Translator(service_urls=['translate.google.com'])
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新正则表达式以匹配未翻译的msgstr
    pattern = r'msgid "(.*?)"\nmsgstr "(.*?)"'
    matches = re.finditer(pattern, content)
    
    updated = False
    for match in matches:
        msgid_text = match.group(1)
        msgstr_text = match.group(2)
        
        # 仅翻译未翻译的msgstr
        if msgstr_text == "":
            if msgid_text in translations:
                translated_text = translations[msgid_text]
                print(f"Using cached translation [{target_lang}]: {msgid_text} -> {translated_text}")
            else:
                try:
                    # 增加重试机制
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            time.sleep(2)  # 增加延迟以避免请求过快
                            # 确保源语言和目标语言设置正确
                            translation = translator.translate(msgid_text, src='auto', dest=target_lang)
                            translated_text = translation.text
                            translations[msgid_text] = translated_text
                            updated = True
                            print(f"New translation [{target_lang}]: {msgid_text} -> {translated_text}")
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                raise e
                            print(f"Retry {attempt + 1}/{max_retries} for: {msgid_text}")
                            time.sleep(5)  # 重试前等待更长时间
                except Exception as e:
                    print(f"Translation failed for: {msgid_text}")
                    print(f"Error: {e}")
                    continue
                
            content = content.replace(
                f'msgid "{msgid_text}"\nmsgstr "{msgstr_text}"',
                f'msgid "{msgid_text}"\nmsgstr "{translated_text}"'
            )
    
    if updated:
        save_translation_cache(cache_file, translations)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    for lang, code in [('en', 'en'), ('fa', 'fa'), ('ru', 'ru')]:
        print(f"\nTranslating to {lang}...")
        translate_po_file(f'po/{lang}.po', f'po/{lang}.po', code)