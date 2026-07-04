def read_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return content


def main():
    content = read_text_file("data/company_docs/employee_handbook.txt")
    print(content)


if __name__ == "__main__":
    main()