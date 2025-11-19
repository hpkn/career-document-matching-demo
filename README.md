<!-- Active the environment -->
python3 -m venv .venv
source .venv/bin/activate

streamlit run app.py


<!-- ai-test.rs-team.com -->

<!-- /etc/systemd/system/career-demo.service -->

<!-- streamlit run app.py --server.port 8501 --server.address 0.0.0.0 -->

domain: https://ai-test.rs-team.com
username: testuser 
password: rsteamCOD001

# 1. Delete all old processed PDFs
sudo systemctl stop career-demo.service

rm /home/rsteam/repositories/career-document-matching-demo/data/pdfs/*.pdf

# 2. Delete all old FAISS index files
rm /home/rsteam/repositories/career-document-matching-demo/data/faiss_index/*
sudo systemctl restart career-demo.service

sudo systemctl status career-demo.service


I am about to ask LLM to restucture an rxisting code to match new requirement. Corect my prompt so, I will have the best result

New requirement: 


Update the full code and Process  in the following way
1. only RUDF
 - Data extraction without OCR
 - Retrive result only for ... as it it now without changing

Once that is done make click on next button
2. Upload file related to 기술경력 
3. extract Data using OCR for PDF. Extract only the following data: 
    - 참영기간
        - (일정일)
        - (참여일일)
    - 사업명
    - 직무분야
    - 담당업무
    - 발주자 | 공사종류
    - 직위

Note: since this part is so important and complex I attached .pdf file as one sample to understand how will the data look. [Only extract data the same page with 1. 기술경력]

4. After the data is extracted and Faiss index made.
- Make a table and show how the extracted data looks with the headers as shown in point 3

5. Show the final result after next button is pressed. 

- The if the user presses Next buton then the final result data should appear. Having the same result data header has in the _form.pdf file 

Restructure for me the full code process and make sure I have the result as required. 