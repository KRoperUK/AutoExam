# AutoExam - Main
import argparse, os, csv, jinja2, pdfkit, segno, re
from time import sleep
from datetime import datetime
from math import floor

MARGIN_SHARED = '1in'

version = "1"

baseTen = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

parser = argparse.ArgumentParser(
                    prog='AutoExam',
                    description='This Python program is used to create and split blank and completed exams.',
                    epilog='Text at the bottom of help')

parserModeGroup = parser.add_mutually_exclusive_group()
parserModeGroup.add_argument('-c', action='store_true')
parserModeGroup.add_argument('-v', action='store_true')

parser.add_argument('--subject', type=str, help='The subject of the exam.')
parser.add_argument('--title', type=str, help='The title of the exam.')
parser.add_argument('--time_allowed', type=str, help='The amount of time allowed for the exam (in minutes).')
parser.add_argument('--year', type=str, help='The year group of the exam.')

def build_pdf(questions: list):
    args = parser.parse_args()
    total_marks = 0

    print(f"\n[AutoExam] Building PDF with {len(questions)} question{'s' if len(questions) > 1 else ''}...")

    context = {}

    if args.subject:
        context['exam_subject'] = args.subject
    else:
        context['exam_subject'] = input("[AutoExam] Enter the exam subject: ")

    if args.title:
        context['exam_title'] = args.title
    else:
        context['exam_title'] = input("[AutoExam] Enter the exam title: ")

    currentDateTime = datetime.now()
    currentDateTime: str = str(currentDateTime)
    currentDateTime = currentDateTime.split('.')[0]
    currentDateTime = currentDateTime.replace(':','-')
    currentDateTime = currentDateTime.replace(' ','_')

    questionsAsHTMLString = ""
    currentSection = 0
    sectionHeader = True


    for question in questions:
        if currentSection != question['section']:
            sectionHeader = True
            currentSection = question['section']
            if currentSection != 1:
                questionsAsHTMLString += """<div class="page-break"></div>"""
            questionsAsHTMLString += f"""<h2 style="text-align:center;">Section {question['section']}</h2><br/>"""
    
        total_marks += int(question['total_marks'])
        qr = segno.make(f"{context['exam_subject']}|{context['exam_title']}|{question['order_question_number']}",
                        micro=False,
                        error='h')
        question_image_filename = f"qrcode-{str(question['order_question_number'])}.svg"
        qr.save(question_image_filename,
                unit='mm',
                scale=15,)

        question_image_filename = os.path.abspath(question_image_filename)

        questionsAsHTMLString += f"""<table class="print-friendly {"question-heading" if (int(question['total_marks']) == 0) and sectionHeader else ""}"><tbody><tr colspan="100%" class="question">"""
        questionsAsHTMLString += """<td class="question question-number question-table-cell">"""
        questionsAsHTMLString += f"{question['display_question_number']}"
        questionsAsHTMLString += f"</td>"

        questionsAsHTMLString += """<td class="question">"""
        questionsAsHTMLString += f"{question['question']}"
        questionsAsHTMLString += f"</td>"

        if int(question['total_marks']) == 0:
            questionsAsHTMLString += f"</tr>"
        else:
            questionsAsHTMLString += """<td class="question question-marks-available">"""
            questionsAsHTMLString += f"[{question['total_marks']}]"
            questionsAsHTMLString += f"""<img src="{question_image_filename}"></img>"""
            questionsAsHTMLString += f"</td>"
            questionsAsHTMLString += f"</tr>"
            questionsAsHTMLString += f"""<tr><td colspan='100%' class='question-break'></td></tr>"""

            if question['format'] in ('short-written', 'long-written', 'short-answer', 'long-answer'):
                questionsAsHTMLString += """<tr class="answer-area"><td colspan="100%" class="answer-area"></td></tr>""" * (floor(int(question['total_marks']) * 1.5) + 1)
            elif question['format'] == 'boolean':
                questionsAsHTMLString += """<tr><td colspan="100%" style="text-align:center;">Yes _____ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; No _____</td></tr>"""
            elif question['format'] == 'multiple-choice':
                choices = question['choices'].strip('][').split(', ')
                questionsAsHTMLString += """<tr><td colspan="100%">"""
                questionsAsHTMLString += """<ul class="multiple-choice">"""
                for choice in choices:
                    questionsAsHTMLString += f"""<li class="multiple-choice"><span class="multiple-choice">☐</span>{choice}</li>"""
                questionsAsHTMLString += """</ul>"""
                questionsAsHTMLString += """</td></tr>"""



        # questionsAsHTMLString += f"""<tr><td colspan='100%' class="question-qr-code"><img src="{question_image_filename}"></img></td></tr>"""


        if question['diagrams'] != "":
            questionsAsHTMLString += """<div class="diagram">"""
            questionsAsHTMLString += f"{question['diagrams']}"
            questionsAsHTMLString += """</div>"""

        questionsAsHTMLString += "</tbody></table>"
        # questionsAsHTMLString += """<div class="page-break"></div>"""
        sectionHeader = False

    context['exam_total_marks'] = total_marks

    context['questions'] = questionsAsHTMLString

    if args.time_allowed:
        context['exam_time_allowed'] = args.time_allowed
    else:
        context['exam_time_allowed'] = str(floor(total_marks * 1.5))

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)

    html_template = 'index.html'
    template = template_env.get_template(html_template)
    output_text = template.render(context)

    with open('log.html', 'w') as htmlLogFile:
        htmlLogFile.write(output_text)
        htmlLogFile.close()

    pdfoptions = {
        'enable-local-file-access': '',
        'margin-top':MARGIN_SHARED,
        'margin-bottom':MARGIN_SHARED,
        'margin-left':MARGIN_SHARED,
        'margin-right':MARGIN_SHARED,
        'page-size':'A4',
        'orientation':'Portrait',
        'encoding':'UTF-8',
        'no-outline':None,
        'dpi':300,
        'image-dpi':300,
        'image-quality':100,
        'footer-right':'[page] of [topage]',
        'footer-center': f'{context["exam_title"]} - {context["exam_subject"]}',}

        # context['exam_time_allowed'] = input("[AutoExam] Enter the time allowed for the exam (minutes): ")
    # filename = currentDateTime + "-exam.pdf"
    filename = f"{context['exam_subject']}_{context['exam_title']}_{currentDateTime}.pdf".replace(' ','_')

    config = pdfkit.configuration()
    pdfkit.from_string(output_text, filename, configuration=config, options=pdfoptions , verbose=True)
    print(f"\n[AutoExam] Created file {filename}")

def create_handle_csv(csv_filename: str):
    try:
        print(f"\n[AutoExam] Handling csv: {csv_filename}")
        with open(csv_filename, newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            
            row_counter = 0
            
            header_row: str

            questions = []

            for row in csv_reader:
                if (row_counter == 0):
                    header_row = row
                else:
                    question = {}
                    question["order_question_number"] = row_counter
                    question["display_question_number"] = row[0]
                    question['total_marks'] = row[1]
                    question['question'] = row[2]
                    question['diagrams'] = row[3]
                    question['format'] = row[4]
                    question['section'] = int(row[5])
                    try:
                        question['choices'] = row[6]
                    except:
                        question['choices'] = ""

                    questions.append(question)
                row_counter += 1

            print("\n[AutoExam] Detected the following headers: ")
            for header in header_row:
                print(f"[AutoExam] - {header}")

            # del csv_reader[0]

            if len(questions) > 0:
                print("\n[AutoExam] Detected the following questions: ")
            else:
                print("\n[AutoExam] No questions detected.")

            for question in questions:
                print(f"[AutoExam] [{str(question['order_question_number'])}] {question['display_question_number']} {question['question']}")

            return build_pdf(questions)

    except Exception as e:
        print("[AutoExam] Error occured when handling CSV file.")
        print("[AutoExam] Debug exception: ", e)
        return False

def mode_create():
    print("\n[AutoExam] Entered create mode.")
    files = os.listdir()

    temp_files = []

    for index, file in enumerate(files):
        try:
            if (file.split('.')[1] == "csv"):
                temp_files.append(file)
        except:
            pass
    files = temp_files
    
    print('final:', files)

    if len(files) < 1:
        print("[AutoExam] No files detected.")
        return False
    elif len(files) == 1:
        return create_handle_csv(files[0])
    elif len(files) < 11:
        print(f"\n[AutoExam] Detected the following files: ")
        for index, csvFile in enumerate(files):
            print(f"[AutoExam] {index + 1}. {csvFile}")
        
        fileSelection: str = '-1'
        while not (fileSelection in baseTen):
            fileSelection = input("\n[AutoExam] Please select a file to use: ")

        fileSelection: int = int(fileSelection) - 1
        # print(fileSelection)

        if fileSelection >= len(files) or fileSelection < 0:
            print("[AutoExam] Invalid input. Please select a file from the list. Restarting...")
            sleep(2)
            return mode_create()
        
        print(f"[AutoExam] You have selected {files[fileSelection]}")
        return create_handle_csv(files[fileSelection])

    else:
        print(f"[AutoExam] More than 10 CSV files detected.")

    


def main():
    print(f"[AutoExam] Running. Version {version}")
    args = parser.parse_args()

    if (args.c):
        # Create mode
        mode_create()
    elif (args.v):
        # View mdoe
        print("[DEBUG] Coming soon.")
    else:
        print("[AutoExam] No mode selected...")

if __name__ == "__main__":
    main()