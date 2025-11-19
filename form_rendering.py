# form_rendering.py
import ast

def checkbox(checked: bool) -> str:
    return "[x]" if bool(checked) else "[ ]"


def render_career_form_markdown(row) -> str:
    """
    Render ONE project's 결과 as a filled 경력인정 적용 가이드 form (Markdown),
    using the exact structure you provided.
    """

    # ----- basic fields from normalized row -----
    section_type = row.get("section_type", "")  # 상주_해당분야 / 기술지원_해당분야 / 상주_직무분야1 / 상주_직무분야2
    participation = row.get("participation_date_type", "참여일")  # "참여일" or "인정일"
    client_category = row.get("client_category", "")              # "기초자치단체", "민간사업", ...
    field_main = row.get("field_main", "")                        # "도로" / "상수도" / "기타토목" ...
    project_name = row.get("project_name", "")
    client_raw = row.get("client_raw", "")
    recognition_rate = float(row.get("recognition_rate", 1.0))

    duties = row.get("duty_checkboxes", [])
    if isinstance(duties, str):
        try:
            duties = ast.literal_eval(duties)
        except Exception:
            duties = [d.strip() for d in duties.split(",") if d.strip()]

    # very simple 발주처 flags (제2조6항은 아직 규칙 없음 → False)
    is_private = (client_category == "민간사업")
    is_je2jo6 = False  # TODO: later detect from text if needed

    # 공종 big category flags
    field_flags = {name: (field_main == name) for name in [
        "도로", "하천", "상수도", "하수도", "철도",
        "단지", "항만", "군부대시설", "조경",
        "기타토목", "전력구", "공항"
    ]}

    # map duty codes (from rules_engine / LLM) → text in form
    code_to_label = {
        "건설사업관리_기술지원": "건설사업관리(기술지원)",
        "건설사업관리_상주": "건설사업관리(상주)",
        "건설사업관리_설계단계": "건설사업관리(설계단계)",
        "시공": "시공",
        "감리": "감리",
        "감독": "감독",
        "관리감독": "관리감독",
        "공사감독": "공사감독설계감독",  # 폼에는 '공사감독설계감독' 하나로 있음
        "시험": "시험검사",
        "검사": "시험검사",
        "유지관리": "유지관리",
        "설계": "설계",
        "기본설계": "기본설계",
        "정밀안전진단": "정밀안전진단",
    }

    duty_checked = {
        "건설사업관리(기술지원)": False,
        "시공": False,
        "감리": False,
        "건설사업관리(상주)": False,
        "건설사업관리(설계단계)": False,
        "감독관리감독": False,
        "공사감독설계감독": False,
        "시공총괄": False,
        "현장공무": False,
        "현장총괄계획": False,
        "시험검사": False,
        "유지관리": False,
        "설계": False,
        "기본설계": False,
        "정밀안전진단": False,
    }

    # fill duty_checked from duty codes
    for code in duties:
        label = code_to_label.get(code)
        if not label:
            continue
        if label in duty_checked:
            duty_checked[label] = True
        # special combined field
        if label == "감독":
            duty_checked["감독관리감독"] = True
        if label == "관리감독":
            duty_checked["감독관리감독"] = True

    lines = []

    # header
    lines.append(f"# 경력인정 적용 가이드 (자동 채움)")
    lines.append("")
    if project_name:
        lines.append(f"- 프로젝트명: **{project_name}**")
    if client_raw:
        lines.append(f"- 발주처: **{client_raw}**")
    lines.append(f"- 분류된 섹션: **{section_type}**")
    lines.append(f"- 인정률: **{int(recognition_rate * 100)}%**")
    lines.append("")
    lines.append("> 책임, 분야별, 기술지원등 각 항목에 경력증명서 업로드")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ============================
    # 상주 해당분야
    # ============================
    lines.append("## 상주 해당분야")
    lines.append("1.  참여일, 인정일 선택")
    lines.append(f"    - {checkbox(participation == '참여일')} 참여일,")
    lines.append(f"    - {checkbox(participation == '인정일')} 인정일")
    lines.append("")
    lines.append("2.  경력 작성에 포함시킬 발주처 선택")
    lines.append(f"    - {checkbox(is_je2jo6)} 제2조6항,")
    lines.append(f"    - {checkbox(is_private)} 민간사업")
    lines.append("    2.1. 제2조6항 선택시")
    lines.append(f"        - {checkbox(False)} 제2조6항 발주처 100%")
    lines.append(f"        - {checkbox(False)} 광역자치단체100%, 기초자치단체60%,")
    lines.append(f"        - {checkbox(False)} 정부투자기관 60%")
    lines.append("")
    lines.append("3.  공종 선택")
    lines.append(f"    - {checkbox(field_flags['도로'])} 도로,")
    lines.append(f"    - {checkbox(field_flags['하천'])} 하천,")
    lines.append(f"    - {checkbox(field_flags['상수도'])} 상수도,")
    lines.append(f"    - {checkbox(field_flags['하수도'])} 하수도,")
    lines.append(f"    - {checkbox(field_flags['철도'])} 철도,")
    lines.append(f"    - {checkbox(field_flags['단지'])} 단지.")
    lines.append(f"    - {checkbox(field_flags['항만'])} 항만,")
    lines.append(f"    - {checkbox(field_flags['군부대시설'])} 군부대시설,")
    lines.append(f"    - {checkbox(field_flags['조경'])} 조경,")
    lines.append(f"    - {checkbox(field_flags['기타토목'])} 기타토목,")
    lines.append(f"    - {checkbox(field_flags['전력구'])} 전력구,")
    lines.append(f"    - {checkbox(field_flags['공항'])} 공항")
    lines.append("")
    lines.append("    3.1. 분야별 세부공종 경력으로 인정할 경력 선택")
    lines.append("        1.  도로 (사업명에 도로, 지방도, 국도, 포함 되었을 때 지하차도 포장 교량 터널 도로분야로 인정)")
    lines.append("            - [ ] 도로")
    lines.append("            - [ ] 국도")
    lines.append("            - [ ] 지방도")
    lines.append("            - [ ] 국지도")
    lines.append("            - [ ] 고속국도(고속도로)")
    lines.append("            - [ ] 지하차도")
    lines.append("            - [ ] 포장")
    lines.append("            - [ ] 교량")
    lines.append("            - [ ] 일반교량")
    lines.append("            - [ ] 터널")
    lines.append("            - [ ] 보도육교")
    lines.append("            - [ ] 확포장도로")
    lines.append("            - [ ] 토목분야(체크공종제외)60%")
    lines.append("        2.  하천")
    lines.append("            - [ ] 하천정비")
    lines.append("            - [ ] 하천정비(국가)")
    lines.append("            - [ ] 하천정비(지방)")
    lines.append("            - [ ] 국가하천지방하천")
    lines.append("            - [ ] 재해위험지구정비하천")
    lines.append("            - [ ] 토목분야(체크공종제외)60%")
    lines.append("        3.  상수도, 하수도")
    lines.append("            - [ ] 상수도 상수도시설")
    lines.append("            - [ ] 상하수도 상수관로 정수장 정수장시설")
    lines.append("            - [ ] 배수관 배수시설 배수지 급수관급수시설 도수관로 송수관")
    lines.append("            - [ ] 오수관로 분뇨처리시설")
    lines.append("            - [ ] 상하수도설비 하수도 하수시설 하수종말처리장 하수저류시설 빗물펌프장")
    lines.append("            - [ ] 하수종말처리시설")
    lines.append("            - [ ] 정수시설")
    lines.append("            - [ ] 송수관로")
    lines.append("            - [ ] 하수관로")
    lines.append("            - [ ] 정수처리")
    lines.append("            - [ ] 송수시설")
    lines.append("            - [ ] 우수관로")
    lines.append("            - [ ] 배수처리시설 폐수종말처리")
    lines.append("            - [ ] 토목분야(체크공종제외)60%")
    lines.append("        4.  철도 (사업명에 철도, 지하철이 포함 되었을 때 교량, 터널, 지하차도(횡단) 철도분야로 인정)")
    lines.append("            - [ ] 철도")
    lines.append("            - [ ] 철도노반시설")
    lines.append("            - [ ] 철도노반")
    lines.append("            - [ ] 지하철")
    lines.append("            - [ ] 경전철")
    lines.append("            - [ ] 일반철도")
    lines.append("            - [ ] 도시철도")
    lines.append("            - [ ] 일반교량")
    lines.append("            - [ ] 교량")
    lines.append("            - [ ] 터널")
    lines.append("            - [ ] 철도[철도노반시설, 철도궤도시설]")
    lines.append("            - [ ] 철도궤도(사업명궤도 포함), 한국도로공사 고속국도, 국토관리청 국도, 지방도, 광역자치단체 국도, 지방도60%")
    lines.append("            - [ ] 철도궤도(사업명궤도 포함), 한국도로공사 고속국도, 국토관리청 국도, 지방도, 광역자치단체 국도, 지방도40%")
    lines.append("            - [ ] (증빙확인) 토목분야(체크공종제외)60%")
    lines.append("        5.  단지")
    lines.append("            - [ ] 단지조성")
    lines.append("            - [ ] 택지개발")
    lines.append("            - [ ] 산업단지조성공사")
    lines.append("            - [ ] 부지조성공사")
    lines.append("            - [ ] 토목분야(기타)60%")
    lines.append("        6.  항만 (전문분야가 무조건 항만및해안)")
    lines.append("            - [ ] 항만")
    lines.append("            - [ ] 항만항만및해안")
    lines.append("            - [ ] 안벽")
    lines.append("            - [ ] 방파제")
    lines.append("            - [ ] 부지조성")
    lines.append("            - [ ] 토목분야(기타)60%")
    lines.append("        7.  조경, 전력구, 공항, 군부대 보류")
    lines.append("")
    lines.append("4.  담당업무 선택")
    lines.append(f"    - {checkbox(duty_checked['건설사업관리(기술지원)'])} 건설사업관리(기술지원)")
    lines.append(f"    - {checkbox(duty_checked['시공'])} 시공")
    lines.append(f"    - {checkbox(duty_checked['감리'])} 감리")
    lines.append(f"    - {checkbox(duty_checked['건설사업관리(상주)'])} 건설사업관리(상주)")
    lines.append(f"    - {checkbox(duty_checked['건설사업관리(설계단계)'])} 건설사업관리(설계단계)")
    lines.append(f"    - {checkbox(duty_checked['감독관리감독'])} 감독관리감독")
    lines.append(f"    - {checkbox(duty_checked['공사감독설계감독'])} 공사감독설계감독")
    lines.append(f"    - {checkbox(duty_checked['시공'])} 시공")
    lines.append(f"    - {checkbox(duty_checked['시공총괄'])} 시공총괄")
    lines.append(f"    - {checkbox(duty_checked['현장공무'])} 현장공무")
    lines.append(f"    - {checkbox(duty_checked['현장총괄계획'])} 현장총괄계획")
    lines.append(f"    - {checkbox(duty_checked['시험검사'])} 시험검사")
    lines.append(f"    - {checkbox(duty_checked['유지관리'])} 유지관리")
    lines.append(f"    - {checkbox(duty_checked['설계'])} 설계")
    lines.append(f"    - {checkbox(duty_checked['기본설계'])} 기본설계")
    lines.append(f"    - {checkbox(duty_checked['정밀안전진단'])} 정밀안전진단")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ============================
    # 기술지원 해당분야
    # ============================
    lines.append("## - 기술지원 해당분야")
    lines.append("")
    lines.append("1.  평가 방법")
    lines.append(f"    - {checkbox(section_type == '기술지원_해당분야')} 상주 평가 방식과 동일")
    lines.append(f"    - {checkbox(section_type == '기술지원_해당분야')} 참여분야의 전문분야 작성")
    lines.append("2.  참여분야의 전문분야 작성시")
    lines.append("    2.1. 참여일, 인정일 선택")
    lines.append(f"        - {checkbox(section_type == '기술지원_해당분야' and participation == '참여일')} 참여일,")
    lines.append(f"        - {checkbox(section_type == '기술지원_해당분야' and participation == '인정일')} 인정일")
    lines.append("    2.2. 경력 작성에 포함시킬 발주처 선택")
    lines.append(f"        - {checkbox(section_type == '기술지원_해당분야' and is_je2jo6)} 제2조6항,")
    lines.append(f"        - {checkbox(section_type == '기술지원_해당분야' and is_private)} 민간사업")
    lines.append("    2.3. 공종 선택")
    lines.append("        - [ ] 도로및공항.")
    lines.append("        - [ ] 토목구조,")
    lines.append("        - [ ] 토질지질,")
    lines.append("        - [ ] 건설안전,")
    lines.append("        - [ ] 조경계획.")
    lines.append("        - [ ] 항만및해안")
    lines.append("        - [ ] 측량및지형공간정보")
    lines.append("        - [ ] 토목품질시험")
    lines.append("        - [ ] 지질및지반")
    lines.append("        - [ ] 건축구조")
    lines.append("        - [ ] 건축기계설비")
    lines.append("        - [ ] 건축시공")
    lines.append("        - [ ] 건축품질시험")
    lines.append("        - [ ] 교통 도시계획")
    lines.append("        - [ ] 토목시공,")
    lines.append("        - [ ] 철도삭도,")
    lines.append("        - [ ] 상하수도,")
    lines.append("        - [ ] 수자원개발.")
    lines.append("        - [ ] 기계")
    lines.append("        - [ ] 건설기계")
    lines.append("        - [ ] 공조냉동기계")
    lines.append("        - [ ] 농어업토목")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ============================
    # 상주 직무분야1
    # ============================
    lines.append("## - 상주 직무분야1")
    lines.append("")
    lines.append("1.  평가 방법")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1')} 직무분야로 평가")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1')} 상주 해당분야 평가 방식과 동일")
    lines.append("2.  직무분야로 평가시")
    lines.append("    - [ ] 토목")
    lines.append("    - [ ] 건축")
    lines.append("    - [ ] 기계")
    lines.append("    - [ ] 안전관리")
    lines.append("")
    lines.append("3.  참여일, 인정일 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and participation in ['참여일','인정일'])} 참여일, 인정일")
    lines.append("")
    lines.append("4.  경력 작성에 포함시킬 발주처 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and is_je2jo6)} 제2조6항,")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and is_private)} 민간사업")
    lines.append("    - [ ] 발주처 빈칸")
    lines.append("5.  담당업무 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['건설사업관리(상주)'])} 건설사업관리(상주)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['건설사업관리(설계단계)'])} 건설사업관리(설계단계)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['건설사업관리(기술지원)'])} 건설사업관리(기술지원)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and '감리' in duties)} 시공감리")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['감독관리감독'])} 감독관리감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['공사감독설계감독'])} 공사감독설계감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['시공'])} 시공")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['시공총괄'])} 시공총괄")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['현장공무'])} 현장공무")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['현장총괄계획'])} 현장총괄계획")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['시험검사'])} 시험검사")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['유지관리'])} 유지관리")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['설계'])} 설계")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['기본설계'])} 기본설계")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야1' and duty_checked['정밀안전진단'])} 정밀안전진단")
    lines.append("6.  경력 인정사항")
    lines.append("    - [ ] 공종 빈칸도 적용")
    lines.append("    - [ ] 담당업무 빈칸도 적용")
    lines.append("    - [ ] 공종 및 담당업무 기재 된 사업만 적용")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ============================
    # 상주 직무분야2
    # ============================
    lines.append("## - 상주 직무분야2")
    lines.append("")
    lines.append("1.  평가 방법")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2')} 직무분야로 평가")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2')} 상주 해당분야 평가 방식과 동일")
    lines.append("2.  직무분야로 평가시")
    lines.append("    - [ ] 토목")
    lines.append("    - [ ] 건축")
    lines.append("    - [ ] 기계")
    lines.append("    - [ ] 조경")
    lines.append("    - [ ] 안전관리")
    lines.append("")
    lines.append("3.  참여일, 인정일 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and participation == '참여일')} 참여일,")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and participation == '인정일')} 인정일")
    lines.append("")
    lines.append("4.  경력 작성에 포함시킬 발주처 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and is_je2jo6)} 제2조6항,")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and is_private)} 민간사업")
    lines.append("    - [ ] 발주처 빈칸")
    lines.append("5.  담당업무 선택")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['건설사업관리(상주)'])} 건설사업관리(상주)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['건설사업관리(설계단계)'])} 건설사업관리(설계단계)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['건설사업관리(기술지원)'])} 건설사업관리(기술지원)")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and '감리' in duties)} 시공감리")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['감독관리감독'])} 감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['감독관리감독'])} 관리감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['공사감독설계감독'])} 공사감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['공사감독설계감독'])} 설계감독")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['시공'])} 시공")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['시공총괄'])} 시공총괄")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['현장공무'])} 현장공무")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['현장총괄계획'])} 현장총괄")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['현장총괄계획'])} 계획")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['시험검사'])} 시험")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['시험검사'])} 검사")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['유지관리'])} 유지관리")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['설계'])} 설계")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['기본설계'])} 기본설계")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['정밀안전진단'])} 실시설계")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['정밀안전진단'])} 타당성조사")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['정밀안전진단'])} 기술자문")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['정밀안전진단'])} 안전점검")
    lines.append(f"    - {checkbox(section_type == '상주_직무분야2' and duty_checked['정밀안전진단'])} 정밀안전진단")
    lines.append("6.  경력 인정사항")
    lines.append("    - [ ] 공종 빈칸도 적용")
    lines.append("    - [ ] 담당업무 빈칸도 적용")
    lines.append("    - [ ] 공종 및 담당업무 기재 된 사업만 적용")

    return "\n".join(lines)
