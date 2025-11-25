# rules_config.py
CHECKBOX_RULES = [
    # === 참여일 / 인정일 선택 (상주 / 기술지원 / 직무분야 공통) ===
    {
        "id": "date.use_participation",
        "label": "참여일 사용",
        "category": "기간",
        "group": "참여일/인정일",
        "logic": { "type": "field_value", "field": "use_date_type", "equals": "participation" },
    },
    {
        "id": "date.use_recognition",
        "label": "인정일 사용",
        "category": "기간",
        "group": "참여일/인정일",
        "logic": { "type": "field_value", "field": "use_date_type", "equals": "recognition" },
    },

    # === 발주처 (상주 / 기술지원 / 직무분야 공통) ===
    # === 2. 경력 작성에 포함시킬 발주처 선택 (필드 변경: client -> client_type) ===
    {
        "id": "orderer.article2_6",
        "label": "경력 작성 발주처 / 제2조6항",
        "category": "발주처",
        "group": "상주/기술지원/직무공통",
        # [FIX] field를 'client_type'으로 변경하여 분류된 결과(기초자치단체 등)와 매칭
        "logic": { "type": "keyword_any", "field": "client_type", "keywords": ["국가", "지방자치단체", "공공기관", "지방공기업", "광역자치단체", "기초자치단체", "정부투자기관", "국토관리청", "한국도로공사", "경기도건설본부"] },
    },
    {
        "id": "orderer.private",
        "label": "경력 작성 발주처 / 민간사업",
        "category": "발주처",
        "group": "상주/기술지원/직무공통",
        "logic": { "type": "keyword_any", "field": "client_type", "keywords": ["민간", "민자", "주식회사", "㈜", "유한회사", "건설", "엔지니어링"] },
    },
    { 
        "id": "orderer.blank", 
        "label": "경력 작성 발주처 / 발주처 빈칸", 
        "category": "발주처", 
        "group": "직무분야 공통", 
        "logic": { "type": "field_value", "field": "client_raw", "equals": "" } 
    },  
    # === 상주 해당분야 / 2.1. 제2조6항 선택시 ===
    { "id": "sangju.orderer.gov_100", "label": "상주 / 제2조6항 발주처 100%", "category": "상주 해당분야", "group": "발주처 세부", "logic": { "type": "keyword_any", "field": "client", "keywords": ["국가", "지방자치단체", "공공기관", "지방공기업", "광역자치단체", "경기도건설본부"] } },
    { 
        "id": "sangju.orderer.local_gov", 
        "label": "상주 / 광역자치단체100%, 기초자치단체60%", 
        "category": "상주 해당분야", "group": "발주처 세부", 
        # "logic": { "type": "keyword_any", "field": "client", "keywords": ["광역자치단체", "기초자치단체", "경기도건설본부"] } 
        "logic": { "type": "keyword_any", "field": "client_type", "keywords": ["광역자치단체", "기초자치단체", "지방자치단체", "경기도건설본부"] }
    },
    
    { "id": "sangju.orderer.gov_invest_60", "label": "상주 / 정부투자기관 60%", "category": "상주 해당분야", "group": "발주처 세부", "logic": { "type": "keyword_any", "field": "client", "keywords": ["정부투자기관"] } },

    # === 상주 해당분야 / 3. 공종 (대분류) ===
    # --- FIX: Check the 'original_fields' list ---
    { "id": "sangju.field.road", "label": "상주 해당분야 / 공종 / 도로", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["도로"] } },
    { "id": "sangju.field.river", "label": "상주 해당분야 / 공종 / 하천", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["하천"] } },
    { "id": "sangju.field.water_supply", "label": "상주 해당분야 / 공종 / 상수도", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["상수도"] } },
    { "id": "sangju.field.water_sewage", "label": "상주 해당분야 / 공종 / 하수도", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["하수도"] } },
    { "id": "sangju.field.railway", "label": "상주 해당분야 / 공종 / 철도", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["철도"] } },
    { "id": "sangju.field.complex", "label": "상주 해당분야 / 공종 / 단지", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["단지"] } },
    { "id": "sangju.field.port", "label": "상주 해당분야 / 공종 / 항만", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["항만"] } },
    { "id": "sangju.field.military", "label": "상주 해당분야 / 공종 / 군부대시설", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["군부대시설"] } },
    { "id": "sangju.field.landscape", "label": "상주 해당분야 / 공종 / 조경", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["조경"] } },
    { "id": "sangju.field.civil_etc", "label": "상주 해당분야 / 공종 / 기타토목", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["기타토목"] } },
    { "id": "sangju.field.power_conduit", "label": "상주 해당분야 / 공종 / 전력구", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["전력구"] } },
    { "id": "sangju.field.airport", "label": "상주 해당분야 / 공종 / 공항", "category": "상주 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["공항"] } },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (도로) ===
    # (These check project_name - this is correct)
    # === 3.1. 세부공종 ===
    { "id": "sangju.field.road.detail.road", "label": "도로/국도/지방도", "category": "상주 해당분야", "group": "도로 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["도로"] } },
    { "id": "sangju.field.road.detail.national_road", "label": "국도", "category": "상주 해당분야", "group": "도로 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["국도"] } },
    { "id": "sangju.field.road.detail.bridge", "label": "교량", "category": "상주 해당분야", "group": "도로 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["교량"] } },
    { "id": "sangju.field.road.detail.tunnel", "label": "터널", "category": "상주 해당분야", "group": "도로 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["터널"] } },
    
    { "id": "sangju.field.river.detail.maintenance", "label": "하천정비", "category": "상주 해당분야", "group": "하천 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["하천"] } },
    
    { "id": "sangju.field.water.detail.supply", "label": "상수도", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["상수도"] } },
    { "id": "sangju.field.water.detail.supply_sewage", "label": "상하수도", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["상하수도"] } },
    { "id": "sangju.field.water.detail.sewage_pipe", "label": "하수도/하수관로", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "original_fields", "keywords": ["하수도"] } },
    # === 상주 해당분야 / 3.1. 분야별 세부공종 (하천) ===
    # ... (all other 3.x sub-fields remain the same, checking project_name or recognition_rate_rule) ...
    { "id": "sangju.field.river.detail.civil_60", "label": "상주 / 하천 / 토목분야(체크공종제외)60%", "category": "상주 해당분야", "group": "하천 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" } },
    { "id": "sangju.field.water.detail.sewer_pipe", "label": "상주 / 하수도 / 하수관로", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하수관로"] } }, 
    { "id": "sangju.field.water.detail.civil_60", "label": "상주 / 상하수도 / 토목분야(체크공종제외)60%", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" } }, 
    { "id": "sangju.field.railway.detail.civil_60", "label": "상주 / 철도 / 토목분야(체크공종제외)60%", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" } },
    { "id": "sangju.field.complex.detail.civil_etc_60", "label": "상주 / 단지 / 토목분야(기타)60%", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_etc_60" } },
    { "id": "sangju.field.port.detail.civil_etc_60", "label": "상주 / 항만 / 토목분야(기타)60%", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_etc_60" } },

    # === 상주 해당분야 / 4. 담당업무 ===
    # --- FIX: Check the 'roles' list ---
    { "id": "sangju.duty.cmc_support", "label": "담당업무 / 건설사업관리(기술지원)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "sangju.duty.construction", "label": "담당업무 / 시공", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공"] } },
    { "id": "sangju.duty.supervision", "label": "담당업무 / 감리", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["감리", "시공감리"] } },
    { "id": "sangju.duty.cmc_resident", "label": "담당업무 / 건설사업관리(상주)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(상주)", "건설사업관리"] } },
    { "id": "sangju.duty.cmc_design_phase", "label": "담당업무 / 건설사업관리(설계단계)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "sangju.duty.director_supervision", "label": "담당업무 / 감독관리감독", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["감독관리감독", "감독", "관리감독", "감독권한대행"] } },
    { "id": "sangju.duty.construction_supervision", "label": "담당업무 / 공사감독설계감독", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["공사감독설계감독", "공사감독", "설계감독"] } },
    { "id": "sangju.duty.construction_management", "label": "담당업무 / 시공총괄", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공총괄"] } },
    { "id": "sangju.duty.site_admin", "label": "담당업무 / 현장공무", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장공무"] } },
    { "id": "sangju.duty.site_management_planning", "label": "담당업무 / 현장총괄계획", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장총괄계획", "현장총괄", "계획"] } },
    { "id": "sangju.duty.test_inspection", "label": "담당업무 / 시험검사", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시험검사", "시험", "검사"] } },
    { "id": "sangju.duty.maintenance", "label": "담당업무 / 유지관리", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["유지관리"] } },
    { "id": "sangju.duty.design", "label": "담당업무 / 설계", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["설계"] } },
    { "id": "sangju.duty.basic_design", "label": "담당업무 / 기본설계", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["기본설계"] } },
    { "id": "sangju.duty.safety_check", "label": "담당업무 / 정밀안전진단", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["정밀안전진단"] } },

    # === 기술지원 해당분야 ===
    { "id": "tech.eval.same_as_sangju", "label": "기술지원 / 상주 평가 방식과 동일", "category": "기술지원 해당분야", "group": "평가 방법", "logic": { "type": "field_value", "field": "tech_eval_method", "equals": "same_as_sangju" } },
    { "id": "tech.eval.use_specialty", "label": "기술지원 / 참여분야의 전문분야 작성", "category": "기술지원 해당분야", "group": "평가 방법", "logic": { "type": "field_value", "field": "tech_eval_method", "equals": "use_specialty" } },
    { "id": "tech.field.road_airport", "label": "기술지원 / 공종 / 도로및공항", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["도로및공항"] } },
    { "id": "tech.field.structure", "label": "기술지원 / 공종 / 토목구조", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["토목구조"] } },
    { "id": "tech.field.geotech", "label": "기술지원 / 공종 / 토질지질", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["토질지질"] } },
    { "id": "tech.field.safety", "label": "기술지원 / 공종 / 건설안전", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건설안전"] } },
    { "id": "tech.field.landscape", "label": "기술지원 / 공종 / 조경계획", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["조경계획"] } },
    { "id": "tech.field.port", "label": "기술지원 / 공종 / 항만및해안", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["항만및해안"] } },
    { "id": "tech.field.survey", "label": "기술지원 / 공종 / 측량및지형공간정보", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["측량및지형공간정보"] } },
    { "id": "tech.field.quality", "label": "기술지원 / 공종 / 토목품질시험", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["토목품질시험"] } },
    { "id": "tech.field.ground", "label": "기술지원 / 공종 / 지질및지반", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["지질및지반"] } },
    { "id": "tech.field.arch_structure", "label": "기술지원 / 공종 / 건축구조", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건축구조"] } },
    { "id": "tech.field.arch_mech", "label": "기술지원 / 공종 / 건축기계설비", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건축기계설비"] } },
    { "id": "tech.field.arch_construct", "label": "기술지원 / 공종 / 건축시공", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건축시공"] } },
    { "id": "tech.field.arch_quality", "label": "기술지원 / 공종 / 건축품질시험", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건축품질시험"] } },
    { "id": "tech.field.transport", "label": "기술지원 / 공종 / 교통", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["교통"] } },
    { "id": "tech.field.urban", "label": "기술지원 / 공종 / 도시계획", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["도시계획"] } },
    { "id": "tech.field.civil_construct", "label": "기술지원 / 공종 / 토목시공", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["토목시공"] } },
    { "id": "tech.field.railway", "label": "기술지원 / 공종 / 철도삭도", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["철도삭도"] } },
    { "id": "tech.field.water", "label": "기술지원 / 공종 / 상하수도", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["상하수도"] } },
    { "id": "tech.field.water_resource", "label": "기술지원 / 공종 / 수자원개발", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["수자원개발"] } },
    { "id": "tech.field.machine", "label": "기술지원 / 공종 / 기계", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["기계"] } },
    { "id": "tech.field.construct_machine", "label": "기술지원 / 공종 / 건설기계", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["건설기계"] } },
    { "id": "tech.field.hvac", "label": "기술지원 / 공종 / 공조냉동기계", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["공조냉동기계"] } },
    { "id": "tech.field.agri_civil", "label": "기술지원 / 공종 / 농어업토목", "category": "기술지원 해당분야", "group": "공종", "logic": { "type": "keyword_any", "field": "specialty", "keywords": ["농어업토목"] } },

    # === 상주 직무분야1 ===
    { "id": "duty_field1.eval.by_duty", "label": "직무분야1 / 직무분야로 평가", "category": "상주 직무분야1", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field1_eval_method", "equals": "by_duty" } },
    { "id": "duty_field1.eval.same_as_sangju", "label": "직무분야1 / 상주 해당분야 평가 방식과 동일", "category": "상주 직무분야1", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field1_eval_method", "equals": "same_as_sangju" } },
    { "id": "duty_field1.field.civil", "label": "직무분야1 / 직무 / 토목", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["토목"] } },
    { "id": "duty_field1.field.architecture", "label": "직무분야1 / 직무 / 건축", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["건축"] } },
    { "id": "duty_field1.field.machine", "label": "직무분야1 / 직무 / 기계", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["기계"] } },
    { "id": "duty_field1.field.safety", "label": "직무분야1 / 직무 / 안전관리", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["안전관리"] } },
    
    # --- FIX: Check the 'roles' list ---
    { "id": "duty_field1.duty.cmc_resident", "label": "직무분야1 / 담당업무 / 건설사업관리(상주)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(상주)", "건설사업관리"] } },
    { "id": "duty_field1.duty.cmc_design_phase", "label": "직무분야1 / 담당업무 / 건설사업관리(설계단계)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "duty_field1.duty.cmc_support", "label": "직무분야1 / 담당업무 / 건설사업관리(기술지원)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "duty_field1.duty.supervision", "label": "직무분야1 / 담당업무 / 시공감리", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공감리"] } },
    { "id": "duty_field1.duty.director_supervision", "label": "직무분야1 / 담당업무 / 감독관리감독", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["감독관리감독", "감독", "관리감독", "감독권한대행"] } },
    { "id": "duty_field1.duty.construction_supervision", "label": "직무분야1 / 담당업무 / 공사감독설계감독", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["공사감독설계감독"] } },
    { "id": "duty_field1.duty.construction", "label": "직무분야1 / 담당업무 / 시공", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공"] } },
    { "id": "duty_field1.duty.construction_mgmt", "label": "직무분야1 / 담당업무 / 시공총괄", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공총괄"] } },
    { "id": "duty_field1.duty.site_admin", "label": "직무분야1 / 담당업무 / 현장공무", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장공무"] } },
    { "id": "duty_field1.duty.site_planning", "label": "직무분야1 / 담당업무 / 현장총괄계획", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장총괄계획"] } },
    { "id": "duty_field1.duty.test_inspection", "label": "직무분야1 / 담당업무 / 시험검사", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시험검사"] } },
    { "id": "duty_field1.duty.maintenance", "label": "직무분야1 / 담당업무 / 유지관리", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["유지관리"] } },
    { "id": "duty_field1.duty.design", "label": "직무분야1 / 담당업무 / 설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["설계"] } },
    { "id": "duty_field1.duty.basic_design", "label": "직무분야1 / 담당업무 / 기본설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["기본설계"] } },
    { "id": "duty_field1.duty.detailed_design", "label": "직무분야1 / 담당업무 / 실시설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["실시설계"] } },
    { "id": "duty_field1.duty.feasibility_study", "label": "직무분야1 / 담당업무 / 타당성조사", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["타당성조사"] } },
    { "id": "duty_field1.duty.technical_advice", "label": "직무분야1 / 담당업무 / 기술자문", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["기술자문"] } },
    { "id": "duty_field1.duty.safety_inspection", "label": "직무분야1 / 담당업무 / 안전점검", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["안전점검"] } },
    { "id": "duty_field1.duty.detailed_safety", "label": "직무분야1 / 담당업무 / 정밀안전진단", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["정밀안전진단"] } },
    { "id": "duty_field1.recognition.include_blank_field", "label": "직무분야1 / 공종 빈칸도 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "include_blank_field" } },
    { "id": "duty_field1.recognition.include_blank_duty", "label": "직무분야1 / 담당업무 빈칸도 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "include_blank_duty" } },
    { "id": "duty_field1.recognition.only_filled", "label": "직무분야1 / 공종 및 담당업무 기재 된 사업만 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "only_filled" } },

    # === 상주 직무분야2 ===
    { "id": "duty_field2.eval.by_duty", "label": "직무분야2 / 직무분야로 평가", "category": "상주 직무분야2", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field2_eval_method", "equals": "by_duty" } },
    { "id": "duty_field2.eval.same_as_sangju", "label": "직무분야2 / 상주 해당분야 평가 방식과 동일", "category": "상주 직무분야2", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field2_eval_method", "equals": "same_as_sangju" } },
    { "id": "duty_field2.field.civil", "label": "직무분야2 / 직무 / 토목", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["토목"] } },
    { "id": "duty_field2.field.architecture", "label": "직무분야2 / 직무 / 건축", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["건축"] } },
    { "id": "duty_field2.field.machine", "label": "직무분야2 / 직무 / 기계", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["기계"] } },
    { "id": "duty_field2.field.landscape", "label": "직무분야2 / 직무 / 조경", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["조경"] } },
    { "id": "duty_field2.field.safety", "label": "직무분야2 / 직무 / 안전관리", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["안전관리"] } },
    
    # --- FIX: Check the 'roles' list ---
    { "id": "duty_field2.duty.cmc_resident", "label": "직무분야2 / 담당업무 / 건설사업관리(상주)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(상주)", "건설사업관리"] } },
    { "id": "duty_field2.duty.cmc_design_phase", "label": "직무분야2 / 담당업무 / 건설사업관리(설계단계)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "duty_field2.duty.cmc_support", "label": "직무분야2 / 담당업무 / 건설사업관리(기술지원)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "duty_field2.duty.supervision", "label": "직무분야2 / 담당업무 / 시공감리", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공감리"] } },
    { "id": "duty_field2.duty.director", "label": "직무분야2 / 담당업무 / 감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["감독", "감독권한대행"] } },
    { "id": "duty_field2.duty.mgmt_supervision", "label": "직무분야2 / 담당업무 / 관리감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["관리감독"] } },
    { "id": "duty_field2.duty.construction_supervision", "label": "직무분야2 / 담당업무 / 공사감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["공사감독"] } },
    { "id": "duty_field2.duty.design_supervision", "label": "직무분야2 / 담당업무 / 설계감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["설계감독"] } },
    { "id": "duty_field2.duty.construction", "label": "직무분야2 / 담당업무 / 시공", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공"] } },
    { "id": "duty_field2.duty.construction_mgmt", "label": "직무분야2 / 담당업무 / 시공총괄", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시공총괄"] } },
    { "id": "duty_field2.duty.site_admin", "label": "직무분야2 / 담당업무 / 현장공무", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장공무"] } },
    { "id": "duty_field2.duty.site_mgmt", "label": "직무분야2 / 담당업무 / 현장총괄", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["현장총괄"] } },
    { "id": "duty_field2.duty.planning", "label": "직무분야2 / 담당업무 / 계획", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["계획"] } },
    { "id": "duty_field2.duty.test", "label": "직무분야2 / 담당업무 / 시험", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["시험"] } },
    { "id": "duty_field2.duty.inspection", "label": "직무분야2 / 담당업무 / 검사", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["검사"] } },
    { "id": "duty_field2.duty.maintenance", "label": "직무분야2 / 담당업무 / 유지관리", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["유지관리"] } },
    { "id": "duty_field2.duty.design", "label": "직무분야2 / 담당업무 / 설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["설계"] } },
    { "id": "duty_field2.duty.basic_design", "label": "직무분야2 / 담당업무 / 기본설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["기본설계"] } },
    { "id": "duty_field2.duty.detailed_design", "label": "직무분야2 / 담당업무 / 실시설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["실시설계"] } },
    { "id": "duty_field2.duty.feasibility_study", "label": "직무분야2 / 담당업무 / 타당성조사", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["타당성조사"] } },
    { "id": "duty_field2.duty.technical_advice", "label": "직무분야2 / 담당업무 / 기술자문", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["기술자문"] } },
    { "id": "duty_field2.duty.safety_inspection", "label": "직무분야2 / 담당업무 / 안전점검", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["안전점검"] } },
    { "id": "duty_field2.duty.detailed_safety", "label": "직무분야2 / 담당업무 / 정밀안전진단", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "roles", "keywords": ["정밀안전진단"] } },

    { "id": "duty_field2.recognition.include_blank_field", "label": "직무분야2 / 공종 빈칸도 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "include_blank_field" } },
    { "id": "duty_field2.recognition.include_blank_duty", "label": "직무분야2 / 담당업무 빈칸도 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "include_blank_duty" } },
    { "id": "duty_field2.recognition.only_filled", "label": "직무분야2 / 공종 및 담당업무 기재 된 사업만 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "only_filled" } },
]

