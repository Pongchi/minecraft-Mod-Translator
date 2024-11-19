import zipfile
import glob
import json
import shutil
import commentjson
import argostranslate.package
import argostranslate.translate
import warnings

warnings.filterwarnings("ignore")

class JsonExporter:
    def __init__(self) -> None:
        self.mod_list = glob.glob("./mod/*.jar")
        self.translated_list = glob.glob("./translated_mod/*.jar")
        # Argos Translate의 번역 언어 설정 (en -> ko)
        self.source_lang = "en"
        self.target_lang = "ko"

    def oneFile(self, _file):
        results = self.postProcessing(_file=_file)
        if results is not None:
            for json_file, lang_path, existing_ko_kr in results:
                print(f"\t└ Translating {lang_path}")
                result_json = self.translate(_json_data=json_file, existing_ko_kr=existing_ko_kr)
                self.saveJar(result_json, _file, lang_path)

    def allFile(self):
        for file in self.mod_list:
            zip_path = file.replace("mod", "translated_mod")
            if zip_path in self.translated_list:
                continue
            zip_path = zip_path.replace(".jar", "_koreanpatch.jar")
            shutil.copy(file, zip_path)

            print(f'[@] Working {zip_path}')
            self.oneFile(zip_path)

    def postProcessing(self, _file: str = "jar_file"):
        results = []
        file_list = zipfile.ZipFile(_file, 'r')
        
        for _file in file_list.namelist():
            if "en_us.json" in _file:
                try:
                    json_file = json.loads(file_list.read(_file))
                except:
                    json_file = commentjson.loads(file_list.read(_file))
                # 대응하는 ko_kr.json 찾기
                ko_kr_file = {}
                ko_kr_path = _file.replace("en_us.json", "ko_kr.json")
                if ko_kr_path in file_list.namelist():
                    try:
                        ko_kr_file = json.loads(file_list.read(ko_kr_path))
                    except:
                        ko_kr_file = commentjson.loads(file_list.read(ko_kr_path))
                results.append((json_file, _file, ko_kr_file))
        
        file_list.close()
        if results:
            return results
        else:
            return None

    def translate(self, _json_data: dict, existing_ko_kr: dict):
        result = existing_ko_kr.copy()  # 기존 ko_kr 내용을 유지
        for _key, _value in _json_data.items():
            if _key in existing_ko_kr:
                continue
            try:
                # Argos Translate 사용
                translated_text = argostranslate.translate.translate(
                    _value, self.source_lang, self.target_lang
                )
                result[_key] = translated_text
            except Exception as e:
                print(f'[!] Error translating key {_key}: {e}')
                result[_key] = _value  # 번역 실패 시 원본 유지
        return result

    def saveJar(self, _result_json: dict, _zip_path: str, _lang_path: str):
        # ko_kr.json 경로
        new_file_path = _lang_path.replace("en_us", "ko_kr")

        # 기존 ZIP 파일을 새 ZIP으로 복사하며 ko_kr.json 제거
        temp_zip_path = _zip_path + ".tmp"
        with zipfile.ZipFile(_zip_path, 'r') as t_jar:
            with zipfile.ZipFile(temp_zip_path, 'w') as temp_zip:
                for item in t_jar.namelist():
                    # 기존 ko_kr.json을 제외하고 나머지 파일 복사
                    if item != new_file_path:
                        temp_zip.writestr(item, t_jar.read(item))

        # 새 ko_kr.json 추가
        with zipfile.ZipFile(temp_zip_path, 'a') as temp_zip:
            temp_zip.writestr(new_file_path, json.dumps(_result_json, indent=4, ensure_ascii=False))

        # 임시 파일을 원본 ZIP 파일로 이동
        shutil.move(temp_zip_path, _zip_path)



def run():
    # Argos Translate 모델 로드
    print("[@] Argos Translate 모델 로드 중...")
    argostranslate.package.install_from_path("translate-en_ko-1_1.argosmodel")  # Argos 모델 설치
    print("[@] 모델 로드 완료.")

    je = JsonExporter()
    je.allFile()


if __name__ == "__main__":
    run()
