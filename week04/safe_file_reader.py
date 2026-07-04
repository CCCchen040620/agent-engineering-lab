from pathlib import Path


def safe_read_text_file(file_path):
    path = Path(file_path)

    if not path.exists():
        return ""

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def main():
    content = safe_read_text_file("data/company_docs/not_exists.txt")

    if content == "":
        print("文件不存在或内容为空。")
    else:
        print(content)


if __name__ == "__main__":
    main()