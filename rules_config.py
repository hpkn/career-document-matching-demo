CHECKBOX_RULES = [
    # === 참여일 / 인정일 선택 (상주 / 기술지원 / 직무분야 공통) ===
    {
        "id": "date.use_participation",
        "label": "참여일 사용",
        "category": "기간",
        "group": "참여일/인정일",
        "logic": {
            "type": "field_value",
            "field": "use_date_type",
            "equals": "participation",
        },
    },
    {
        "id": "date.use_recognition",
        "label": "인정일 사용",
        "category": "기간",
        "group": "참여일/인정일",
        "logic": {
            "type": "field_value",
            "field": "use_date_type",
            "equals": "recognition",
        },
    },

    # === 발주처 (상주 / 기술지원 / 직무분야 공통) ===
    {
        "id": "orderer.article2_6",
        "label": "경력 작성 발주처 / 제2조6항",
        "category": "발주처",
        "group": "상주/기술지원/직무공통",
        "logic": {
            "type": "keyword_any",
            "field": "client",
            # "제2조6항 발주처 100%", "광역자치단체100%", "기초자치단체60%", "정부투자기관 60%"
            "keywords": ["국가", "지방자치단체", "공공기관", "지방공기업", "광역자치단체", "기초자치단체", "정부투자기관", "국토관리청", "한국도로공사"],
        },
    },
    {
        "id": "orderer.private",
        "label": "경력 작성 발주처 / 민간사업",
        "category": "발주처",
        "group": "상주/기술지원/직무공통",
        "logic": {
            "type": "keyword_any",
            "field": "client",
            "keywords": ["민간", "민자", "주식회사", "㈜", "유한회사"],
        },
    },
    # --- 상주 직무분야 1/2 공통 ---
    {
        "id": "orderer.blank",
        "label": "경력 작성 발주처 / 발주처 빈칸",
        "category": "발주처",
        "group": "직무분야 공통",
        "logic": {
            "type": "field_value",
            "field": "client",
            "equals": "", # Assumes blank client field
        },
    },

    # === 상주 해당분야 / 2.1. 제2조6항 선택시 ===
    {
        "id": "sangju.orderer.gov_100",
        "label": "상주 / 제2조6항 발주처 100%",
        "category": "상주 해당분야",
        "group": "발주처 세부",
        "logic": {
            "type": "keyword_any",
            "field": "client",
            "keywords": ["국가", "지방자치단체", "공공기관", "지방공기업"], # 100% categories
        },
    },
    {
        "id": "sangju.orderer.local_gov",
        "label": "상주 / 광역자치단체100%, 기초자치단체60%",
        "category": "상주 해당분야",
        "group": "발주처 세부",
        "logic": {
            "type": "keyword_any",
            "field": "client",
            "keywords": ["광역자치단체", "기초자치단체"],
        },
    },
    {
        "id": "sangju.orderer.gov_invest_60",
        "label": "상주 / 정부투자기관 60%",
        "category": "상주 해당분야",
        "group": "발주처 세부",
        "logic": {
            "type": "keyword_any",
            "field": "client",
            "keywords": ["정부투자기관"],
        },
    },

    # === 상주 해당분야 / 3. 공종 (대분류) ===
    {
        "id": "sangju.field.road",
        "label": "상주 해당분야 / 공종 / 도로",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["도로", "국도", "지방도", "국지도", "고속국도", "고속도로"],
        },
    },
    {
        "id": "sangju.field.river",
        "label": "상주 해당분야 / 공종 / 하천",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["하천정비", "하천", "국가하천", "지방하천", "재해위험지구정비하천"],
        },
    },
    {
        "id": "sangju.field.water_supply",
        "label": "상주 해당분야 / 공종 / 상수도",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["상수도", "상수관로", "정수장", "급수관", "도수관로", "송수관"],
        },
    },
    {
        "id": "sangju.field.water_sewage",
        "label": "상주 해당분야 / 공종 / 하수도",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["하수도", "하수시설", "하수종말처리장", "오수관로", "하수관로", "우수관로"],
        },
    },
    {
        "id": "sangju.field.railway",
        "label": "상주 해당분야 / 공종 / 철도",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["철도", "지하철", "경전철", "도시철도"],
        },
    },
    {
        "id": "sangju.field.complex",
        "label": "상주 해당분야 / 공종 / 단지",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["단지", "택지개발", "산업단지", "부지조성"],
        },
    },
    {
        "id": "sangju.field.port",
        "label": "상주 해당분야 / 공종 / 항만",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": {
            "type": "keyword_any",
            "field": "project_name",
            "keywords": ["항만", "항만및해안", "안벽", "방파제"],
        },
    },
    {
        "id": "sangju.field.military",
        "label": "상주 해당분야 / 공종 / 군부대시설",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["군부대"] },
    },
    {
        "id": "sangju.field.landscape",
        "label": "상주 해당분야 / 공종 / 조경",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["조경"] },
    },
    {
        "id": "sangju.field.civil_etc",
        "label": "상주 해당분야 / 공종 / 기타토목",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["기타토목"] },
    },
    {
        "id": "sangju.field.power_conduit",
        "label": "상주 해당분야 / 공종 / 전력구",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["전력구"] },
    },
    {
        "id": "sangju.field.airport",
        "label": "상주 해당분야 / 공종 / 공항",
        "category": "상주 해당분야",
        "group": "공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["공항"] },
    },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (도로) ===
    {
        "id": "sangju.field.road.detail.road",
        "label": "상주 / 도로 / 도로",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["도로"] },
    },
    {
        "id": "sangju.field.road.detail.national_road",
        "label": "상주 / 도로 / 국도",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["국도"] },
    },
    {
        "id": "sangju.field.road.detail.local_road",
        "label": "상주 / 도로 / 지방도",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["지방도"] },
    },
    {
        "id": "sangju.field.road.detail.gukjido",
        "label": "상주 / 도로 / 국지도",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["국지도"] },
    },
    {
        "id": "sangju.field.road.detail.expressway",
        "label": "상주 / 도로 / 고속국도(고속도로)",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["고속국도", "고속도로"] },
    },
    {
        "id": "sangju.field.road.detail.underpass",
        "label": "상주 / 도로 / 지하차도",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["지하차도"] },
    },
    {
        "id": "sangju.field.road.detail.pavement",
        "label": "상주 / 도로 / 포장",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["포장"] },
    },
    {
        "id": "sangju.field.road.detail.bridge",
        "label": "상주 / 도로 / 교량",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["교량"] },
    },
    {
        "id": "sangju.field.road.detail.general_bridge",
        "label": "상주 / 도로 / 일반교량",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["일반교량"] },
    },
    {
        "id": "sangju.field.road.detail.tunnel",
        "label": "상주 / 도로 / 터널",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["터널"] },
    },
    {
        "id": "sangju.field.road.detail.overpass",
        "label": "상주 / 도로 / 보도육교",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["보도육교"] },
    },
    {
        "id": "sangju.field.road.detail.expansion",
        "label": "상주 / 도로 / 확포장도로",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["확포장도로"] },
    },
    {
        "id": "sangju.field.road.detail.civil_60",
        "label": "상주 / 도로 / 토목분야(체크공종제외)60%",
        "category": "상주 해당분야", "group": "도로 세부공종",
        "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" },
    },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (하천) ===
    {
        "id": "sangju.field.river.detail.maintenance",
        "label": "상주 / 하천 / 하천정비",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하천정비"] },
    },
    {
        "id": "sangju.field.river.detail.maintenance_nat",
        "label": "상주 / 하천 / 하천정비(국가)",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하천정비(국가)"] },
    },
    {
        "id": "sangju.field.river.detail.maintenance_loc",
        "label": "상주 / 하천 / 하천정비(지방)",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하천정비(지방)"] },
    },
    {
        "id": "sangju.field.river.detail.nat_loc",
        "label": "상주 / 하천 / 국가하천지방하천",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["국가하천", "지방하천"] },
    },
    {
        "id": "sangju.field.river.detail.disaster",
        "label": "상주 / 하천 / 재해위험지구정비하천",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["재해위험지구정비하천"] },
    },
    {
        "id": "sangju.field.river.detail.civil_60",
        "label": "상주 / 하천 / 토목분야(체크공종제외)60%",
        "category": "상주 해당분야", "group": "하천 세부공종",
        "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" },
    },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (상수도, 하수도) ===
    {
        "id": "sangju.field.water.detail.supply",
        "label": "상주 / 상수도 / 상수도 상수도시설",
        "category": "상주 해당분야", "group": "상하수도 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["상수도", "상수도시설"] },
    },
    {
        "id": "sangju.field.water.detail.supply_sewage",
        "label": "상주 / 상수도 / 상하수도 상수관로 정수장 정수장시설",
        "category": "상주 해당분야", "group": "상하수도 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["상하수도", "상수관로", "정수장", "정수장시설"] },
    },
    {
        "id": "sangju.field.water.detail.drainage",
        "label": "상주 / 상수도 / 배수관 배수시설 배수지 급수관급수시설 도수관로 송수관",
        "category": "상주 해당분야", "group": "상하수도 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["배수관", "배수시설", "배수지", "급수관", "급수시설", "도수관로", "송수관"] },
    },
    {
        "id": "sangju.field.water.detail.sewage_pipe",
        "label": "상주 / 하수도 / 오수관로 분뇨처리시설",
        "category": "상주 해당분야", "group": "상하수도 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["오수관로", "분뇨처리시설"] },
    },
    {
        "id": "sangju.field.water.detail.sewage_facility",
        "label": "상주 / 하수도 / 상하수도설비 하수도 하수시설 하수종말처리장 하수저류시설 빗물펌프장",
        "category": "상주 해당분야", "group": "상하수도 세부공종",
        "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["상하수도설비", "하수도", "하수시설", "하수종말처리장", "하수저류시설", "빗물펌프장"] },
    },
    { "id": "sangju.field.water.detail.sewage_final", "label": "상주 / 하수도 / 하수종말처리시설", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하수종말처리시설"] } },
    { "id": "sangju.field.water.detail.purify_facility", "label": "상주 / 상수도 / 정수시설", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["정수시설"] } },
    { "id": "sangju.field.water.detail.transmission_pipe", "label": "상주 / 상수도 / 송수관로", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["송수관로"] } },
    { "id": "sangju.field.water.detail.sewer_pipe", "label": "상주 / 하수도 / 하수관로", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["하수관로"] } },
    { "id": "sangju.field.water.detail.purify_process", "label": "상주 / 상수도 / 정수처리", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["정수처리"] } },
    { "id": "sangju.field.water.detail.transmission_facility", "label": "상주 / 상수도 / 송수시설", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["송수시설"] } },
    { "id": "sangju.field.water.detail.storm_pipe", "label": "상주 / 하수도 / 우수관로", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["우수관로"] } },
    { "id": "sangju.field.water.detail.drainage_facility", "label": "상주 / 하수도 / 배수처리시설", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["배수처리시설"] } },
    { "id": "sangju.field.water.detail.waste_water", "label": "상주 / 하수도 / 폐수종말처리", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["폐수종말처리"] } },
    { "id": "sangju.field.water.detail.civil_60", "label": "상주 / 상하수도 / 토목분야(체크공종제외)60%", "category": "상주 해당분야", "group": "상하수도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" } },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (철도) ===
    { "id": "sangju.field.railway.detail.railway", "label": "상주 / 철도 / 철도", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["철도"] } },
    { "id": "sangju.field.railway.detail.roadbed_facility", "label": "상주 / 철도 / 철도노반시설", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["철도노반시설"] } },
    { "id": "sangju.field.railway.detail.roadbed", "label": "상주 / 철도 / 철도노반", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["철도노반"] } },
    { "id": "sangju.field.railway.detail.subway", "label": "상주 / 철도 / 지하철", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["지하철"] } },
    { "id": "sangju.field.railway.detail.light_rail", "label": "상주 / 철도 / 경전철", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["경전철"] } },
    { "id": "sangju.field.railway.detail.general_rail", "label": "상주 / 철도 / 일반철도", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["일반철도"] } },
    { "id": "sangju.field.railway.detail.urban_rail", "label": "상주 / 철도 / 도시철도", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["도시철도"] } },
    { "id": "sangju.field.railway.detail.general_bridge", "label": "상주 / 철도 / 일반교량", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["일반교량"] } },
    { "id": "sangju.field.railway.detail.bridge", "label": "상주 / 철도 / 교량", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["교량"] } },
    { "id": "sangju.field.railway.detail.tunnel", "label": "상주 / 철도 / 터널", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["터널"] } },
    { "id": "sangju.field.railway.detail.facilities_combined", "label": "상주 / 철도 / 철도[철도노반시설, 철도궤도시설]", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["철도노반시설", "철도궤도시설"] } },
    { "id": "sangju.field.railway.detail.track_60", "label": "상주 / 철도 / 철도궤도...60%", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "track_60" } },
    { "id": "sangju.field.railway.detail.track_40", "label": "상주 / 철도 / 철도궤도...40%", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "track_40" } },
    { "id": "sangju.field.railway.detail.civil_60", "label": "상주 / 철도 / 토목분야(체크공종제외)60%", "category": "상주 해당분야", "group": "철도 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_60" } },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (단지) ===
    { "id": "sangju.field.complex.detail.land_dev", "label": "상주 / 단지 / 단지조성", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["단지조성"] } },
    { "id": "sangju.field.complex.detail.housing_dev", "label": "상주 / 단지 / 택지개발", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["택지개발"] } },
    { "id": "sangju.field.complex.detail.industrial_dev", "label": "상주 / 단지 / 산업단지조성공사", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["산업단지조성"] } },
    { "id": "sangju.field.complex.detail.site_prep", "label": "상주 / 단지 / 부지조성공사", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["부지조성"] } },
    { "id": "sangju.field.complex.detail.civil_etc_60", "label": "상주 / 단지 / 토목분야(기타)60%", "category": "상주 해당분야", "group": "단지 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_etc_60" } },

    # === 상주 해당분야 / 3.1. 분야별 세부공종 (항만) ===
    { "id": "sangju.field.port.detail.port", "label": "상주 / 항만 / 항만", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["항만"] } },
    { "id": "sangju.field.port.detail.port_coast", "label": "상주 / 항만 / 항만항만및해안", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["항만및해안"] } },
    { "id": "sangju.field.port.detail.quay", "label": "상주 / 항만 / 안벽", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["안벽"] } },
    { "id": "sangju.field.port.detail.breakwater", "label": "상주 / 항만 / 방파제", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["방파제"] } },
    { "id": "sangju.field.port.detail.site_prep", "label": "상주 / 항만 / 부지조성", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "keyword_any", "field": "project_name", "keywords": ["부지조성"] } },
    { "id": "sangju.field.port.detail.civil_etc_60", "label": "상주 / 항만 / 토목분야(기타)60%", "category": "상주 해당분야", "group": "항만 세부공종", "logic": { "type": "field_value", "field": "recognition_rate_rule", "equals": "civil_etc_60" } },

    # === 상주 해당분야 / 4. 담당업무 ===
    { "id": "sangju.duty.cmc_support", "label": "담당업무 / 건설사업관리(기술지원)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "sangju.duty.construction", "label": "담당업무 / 시공", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공"] } },
    { "id": "sangju.duty.supervision", "label": "담당업무 / 감리", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["감리", "시공감리"] } },
    { "id": "sangju.duty.cmc_resident", "label": "담당업무 / 건설사업관리(상주)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(상주)"] } },
    { "id": "sangju.duty.cmc_design_phase", "label": "담당업무 / 건설사업관리(설계단계)", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "sangju.duty.director_supervision", "label": "담당업무 / 감독관리감독", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["감독관리감독", "감독", "관리감독"] } },
    { "id": "sangju.duty.construction_supervision", "label": "담당업무 / 공사감독설계감독", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["공사감독설계감독", "공사감독", "설계감독"] } },
    { "id": "sangju.duty.construction_management", "label": "담당업무 / 시공총괄", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공총괄"] } },
    { "id": "sangju.duty.site_admin", "label": "담당업무 / 현장공무", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장공무"] } },
    { "id": "sangju.duty.site_management_planning", "label": "담당업무 / 현장총괄계획", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장총괄계획", "현장총괄", "계획"] } },
    { "id": "sangju.duty.test_inspection", "label": "담당업무 / 시험검사", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시험검사", "시험", "검사"] } },
    { "id": "sangju.duty.maintenance", "label": "담당업무 / 유지관리", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["유지관리"] } },
    { "id": "sangju.duty.design", "label": "담당업무 / 설계", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["설계"] } },
    { "id": "sangju.duty.basic_design", "label": "담당업무 / 기본설계", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["기본설계"] } },
    { "id": "sangju.duty.safety_check", "label": "담당업무 / 정밀안전진단", "category": "상주 해당분야", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["정밀안전진단"] } },

    # === 기술지원 해당분야 / 1. 평가 방법 ===
    { "id": "tech.eval.same_as_sangju", "label": "기술지원 / 상주 평가 방식과 동일", "category": "기술지원 해당분야", "group": "평가 방법", "logic": { "type": "field_value", "field": "tech_eval_method", "equals": "same_as_sangju" } },
    { "id": "tech.eval.use_specialty", "label": "기술지원 / 참여분야의 전문분야 작성", "category": "기술지원 해당분야", "group": "평가 방법", "logic": { "type": "field_value", "field": "tech_eval_method", "equals": "use_specialty" } },

    # === 기술지원 해당분야 / 2.3 공종 선택 ===
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

    # === 상주 직무분야1 / 1. 평가 방법 ===
    { "id": "duty_field1.eval.by_duty", "label": "직무분야1 / 직무분야로 평가", "category": "상주 직무분야1", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field1_eval_method", "equals": "by_duty" } },
    { "id": "duty_field1.eval.same_as_sangju", "label": "직무분야1 / 상주 해당분야 평가 방식과 동일", "category": "상주 직무분야1", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field1_eval_method", "equals": "same_as_sangju" } },
    
    # === 상주 직무분야1 / 2. 직무분야로 평가시 ===
    { "id": "duty_field1.field.civil", "label": "직무분야1 / 직무 / 토목", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["토목"] } },
    { "id": "duty_field1.field.architecture", "label": "직무분야1 / 직무 / 건축", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["건축"] } },
    { "id": "duty_field1.field.machine", "label": "직무분야1 / 직무 / 기계", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["기계"] } },
    { "id": "duty_field1.field.safety", "label": "직무분야1 / 직무 / 안전관리", "category": "상주 직무분야1", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field1", "keywords": ["안전관리"] } },
    
    # === 상주 직무분야1 / 5. 담당업무 ===
    # (Many are covered by 'sangju.duty' rules, adding missing ones)
    { "id": "duty_field1.duty.cmc_resident", "label": "직무분야1 / 담당업무 / 건설사업관리(상주)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(상주)"] } },
    { "id": "duty_field1.duty.cmc_design_phase", "label": "직무분야1 / 담당업무 / 건설사업관리(설계단계)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "duty_field1.duty.cmc_support", "label": "직무분야1 / 담당업무 / 건설사업관리(기술지원)", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "duty_field1.duty.supervision", "label": "직무분야1 / 담당업무 / 시공감리", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공감리"] } },
    { "id": "duty_field1.duty.director_supervision", "label": "직무분야1 / 담당업무 / 감독관리감독", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["감독관리감독"] } },
    { "id": "duty_field1.duty.construction_supervision", "label": "직무분야1 / 담당업무 / 공사감독설계감독", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["공사감독설계감독"] } },
    { "id": "duty_field1.duty.construction", "label": "직무분야1 / 담당업무 / 시공", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공"] } },
    { "id": "duty_field1.duty.construction_mgmt", "label": "직무분야1 / 담당업무 / 시공총괄", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공총괄"] } },
    { "id": "duty_field1.duty.site_admin", "label": "직무분야1 / 담당업무 / 현장공무", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장공무"] } },
    { "id": "duty_field1.duty.site_planning", "label": "직무분야1 / 담당업무 / 현장총괄계획", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장총괄계획"] } },
    { "id": "duty_field1.duty.test_inspection", "label": "직무분야1 / 담당업무 / 시험검사", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시험검사"] } },
    { "id": "duty_field1.duty.maintenance", "label": "직무분야1 / 담당업무 / 유지관리", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["유지관리"] } },
    { "id": "duty_field1.duty.design", "label": "직무분야1 / 담당업무 / 설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["설계"] } },
    { "id": "duty_field1.duty.basic_design", "label": "직무분야1 / 담당업무 / 기본설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["기본설계"] } },
    { "id": "duty_field1.duty.detailed_design", "label": "직무분야1 / 담당업무 / 실시설계", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["실시설계"] } },
    { "id": "duty_field1.duty.feasibility_study", "label": "직무분야1 / 담당업무 / 타당성조사", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["타당성조사"] } },
    { "id": "duty_field1.duty.technical_advice", "label": "직무분야1 / 담당업무 / 기술자문", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["기술자문"] } },
    { "id": "duty_field1.duty.safety_inspection", "label": "직무분야1 / 담당업무 / 안전점검", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["안전점검"] } },
    { "id": "duty_field1.duty.detailed_safety", "label": "직무분야1 / 담당업무 / 정밀안전진단", "category": "상주 직무분야1", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["정밀안전진단"] } },

    # === 상주 직무분야1 / 6. 경력 인정사항 ===
    { "id": "duty_field1.recognition.include_blank_field", "label": "직무분야1 / 공종 빈칸도 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "include_blank_field" } },
    { "id": "duty_field1.recognition.include_blank_duty", "label": "직무분야1 / 담당업무 빈칸도 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "include_blank_duty" } },
    { "id": "duty_field1.recognition.only_filled", "label": "직무분야1 / 공종 및 담당업무 기재 된 사업만 적용", "category": "상주 직무분야1", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field1_recognition_rule", "equals": "only_filled" } },

    # === 상주 직무분야2 / 1. 평가 방법 ===
    { "id": "duty_field2.eval.by_duty", "label": "직무분야2 / 직무분야로 평가", "category": "상주 직무분야2", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field2_eval_method", "equals": "by_duty" } },
    { "id": "duty_field2.eval.same_as_sangju", "label": "직무분야2 / 상주 해당분야 평가 방식과 동일", "category": "상주 직무분야2", "group": "평가 방법", "logic": { "type": "field_value", "field": "duty_field2_eval_method", "equals": "same_as_sangju" } },
    
    # === 상주 직무분야2 / 2. 직무분야로 평가시 ===
    { "id": "duty_field2.field.civil", "label": "직무분야2 / 직무 / 토목", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["토목"] } },
    { "id": "duty_field2.field.architecture", "label": "직무분야2 / 직무 / 건축", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["건축"] } },
    { "id": "duty_field2.field.machine", "label": "직무분야2 / 직무 / 기계", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["기계"] } },
    { "id": "duty_field2.field.landscape", "label": "직무분야2 / 직무 / 조경", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["조경"] } },
    { "id": "duty_field2.field.safety", "label": "직무분야2 / 직무 / 안전관리", "category": "상주 직무분야2", "group": "직무분야", "logic": { "type": "keyword_any", "field": "duty_field2", "keywords": ["안전관리"] } },
    
    # === 상주 직무분야2 / 5. 담당업무 ===
    { "id": "duty_field2.duty.cmc_resident", "label": "직무분야2 / 담당업무 / 건설사업관리(상주)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(상주)"] } },
    { "id": "duty_field2.duty.cmc_design_phase", "label": "직무분야2 / 담당업무 / 건설사업관리(설계단계)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(설계단계)"] } },
    { "id": "duty_field2.duty.cmc_support", "label": "직무분야2 / 담당업무 / 건설사업관리(기술지원)", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["건설사업관리(기술지원)"] } },
    { "id": "duty_field2.duty.supervision", "label": "직무분야2 / 담당업무 / 시공감리", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공감리"] } },
    { "id": "duty_field2.duty.director", "label": "직무분야2 / 담당업무 / 감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["감독"] } },
    { "id": "duty_field2.duty.mgmt_supervision", "label": "직무분야2 / 담당업무 / 관리감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["관리감독"] } },
    { "id": "duty_field2.duty.construction_supervision", "label": "직무분야2 / 담당업무 / 공사감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["공사감독"] } },
    { "id": "duty_field2.duty.design_supervision", "label": "직무분야2 / 담당업무 / 설계감독", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["설계감독"] } },
    { "id": "duty_field2.duty.construction", "label": "직무분야2 / 담당업무 / 시공", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공"] } },
    { "id": "duty_field2.duty.construction_mgmt", "label": "직무분야2 / 담당업무 / 시공총괄", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시공총괄"] } },
    { "id": "duty_field2.duty.site_admin", "label": "직무분야2 / 담당업무 / 현장공무", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장공무"] } },
    { "id": "duty_field2.duty.site_mgmt", "label": "직무분야2 / 담당업무 / 현장총괄", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["현장총괄"] } },
    { "id": "duty_field2.duty.planning", "label": "직무분야2 / 담당업무 / 계획", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["계획"] } },
    { "id": "duty_field2.duty.test", "label": "직무분야2 / 담당업무 / 시험", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["시험"] } },
    { "id": "duty_field2.duty.inspection", "label": "직무분야2 / 담당업무 / 검사", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["검사"] } },
    { "id": "duty_field2.duty.maintenance", "label": "직무분야2 / 담당업무 / 유지관리", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["유지관리"] } },
    { "id": "duty_field2.duty.design", "label": "직무분야2 / 담당업무 / 설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["설계"] } },
    { "id": "duty_field2.duty.basic_design", "label": "직무분야2 / 담당업무 / 기본설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["기본설계"] } },
    { "id": "duty_field2.duty.detailed_design", "label": "직무분야2 / 담당업무 / 실시설계", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["실시설계"] } },
    { "id": "duty_field2.duty.feasibility_study", "label": "직무분야2 / 담당업무 / 타당성조사", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["타당성조사"] } },
    { "id": "duty_field2.duty.technical_advice", "label": "직무분야2 / 담당업무 / 기술자문", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["기술자문"] } },
    { "id": "duty_field2.duty.safety_inspection", "label": "직무분야2 / 담당업무 / 안전점검", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["안전점검"] } },
    { "id": "duty_field2.duty.detailed_safety", "label": "직무분야2 / 담당업무 / 정밀안전진단", "category": "상주 직무분야2", "group": "담당업무", "logic": { "type": "keyword_any", "field": "role", "keywords": ["정밀안전진단"] } },

    # === 상주 직무분야2 / 6. 경력 인정사항 ===
    { "id": "duty_field2.recognition.include_blank_field", "label": "직무분야2 / 공종 빈칸도 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "include_blank_field" } },
    { "id": "duty_field2.recognition.include_blank_duty", "label": "직무분야2 / 담당업무 빈칸도 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "include_blank_duty" } },
    { "id": "duty_field2.recognition.only_filled", "label": "직무분야2 / 공종 및 담당업무 기재 된 사업만 적용", "category": "상주 직무분야2", "group": "경력 인정사항", "logic": { "type": "field_value", "field": "duty_field2_recognition_rule", "equals": "only_filled" } },

]