import requests
import json
import logging
import time
import os

# ---------------------------
# 共通: Notion API 設定
# ---------------------------

def get_notion_headers():
    notion_token = os.environ.get("NOTION_TOKEN")
    if not notion_token:
        raise ValueError("NOTION_TOKEN environment variable is not set")
    return {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

# ---------------------------
# Notion ページ検索ユーティリティ
# ---------------------------

def search_notion_page(database_id: str, rec_no: int) -> str:
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {"filter": {"property": "レコード番号", "number": {"equals": rec_no}}}
    headers = get_notion_headers()

    for retry in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload)
            if r.status_code == 429:
                time.sleep(2 ** retry)
                continue
            r.raise_for_status()
            results = r.json().get("results", [])
            return results[0]["id"] if results else None
        except Exception as e:
            print(f"Notion検索エラー: {str(e)}")
            return None

# ---------------------------
# 共通処理関数
# ---------------------------

def process_records(filter_date: str, k_sub: str, k_app: str, k_token: str, notion_db_id: str, field_mapping: dict):
    # レコード取得処理
    def fetch_kintone_records(query_filter):
        records = []
        limit, offset = 100, 0

        while True:
            try:
                params = {
                    "app": k_app,
                    "query": f'{query_filter} >= "{filter_date}T00:00:00Z" order by 更新日時 asc limit {limit} offset {offset}',
                }
                
                response = requests.get(
                    f"https://{k_sub}.cybozu.com/k/v1/records.json",
                    headers={"X-Cybozu-API-Token": k_token},
                    json=params,
                    timeout=10
                )
                response.raise_for_status()
                batch = response.json().get("records", [])
                
                if not batch:
                    break
                    
                records.extend(batch)
                if len(batch) < limit:
                    break
                offset += limit
                time.sleep(0.5)
                
            except Exception as e:
                print(f"キントーン取得エラー: {str(e)}")
                break
                
        return records

    # レコード取得
    print(f"[{k_app}] 更新日時基準のレコード取得開始")
    updated_records = fetch_kintone_records("更新日時")
    print(f"[{k_app}] 更新対象レコード数: {len(updated_records)}件")

    print(f"[{k_app}] 作成日時基準のレコード取得開始")
    created_records = fetch_kintone_records("作成日時")
    print(f"[{k_app}] 新規作成対象レコード数: {len(created_records)}件")

    # レコード統合と重複排除
    seen_ids = set()
    all_records = []

    for rec in updated_records:
        rec_id = rec["$id"]["value"]
        if rec_id not in seen_ids:
            seen_ids.add(rec_id)
            all_records.append(rec)

    for rec in created_records:
        rec_id = rec["$id"]["value"]
        if rec_id not in seen_ids:
            seen_ids.add(rec_id)
            all_records.append(rec)

    print(f"[{k_app}] 総処理レコード数: {len(all_records)}件")

    # レコード処理
    created_count = updated_count = errors_count = 0
    logs = []

    print(f"[{k_app}] レコード処理開始")
    headers = get_notion_headers()

    for rec in all_records:
        try:
            rec_no = int(rec["$id"]["value"])
            # print(f"処理中 (ID={rec_no})")
            page_id = search_notion_page(notion_db_id, rec_no)
            props = create_properties(rec, field_mapping)

            if page_id:  # 更新処理
                response = requests.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=headers,
                    json={"properties": props},
                    timeout=10
                )
                if response.ok:
                    updated_count += 1
                    # print(f"🔄 更新成功 (ID={rec_no})")
                else:
                    raise Exception(f"Status: {response.status_code}")
            else:  # 新規作成
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json={"parent": {"database_id": notion_db_id}, "properties": props},
                    timeout=10
                )
                if response.ok:
                    created_count += 1
                    # print(f"✅ 新規作成 (ID={rec_no})")
                else:
                    raise Exception(f"Status: {response.status_code}")

        except Exception as e:
            errors_count += 1
            print(f"⚠️ エラー発生 (ID={rec_no}): {str(e)}")
            logs.append(f"Error ID={rec_no}: {str(e)}")

    return created_count, updated_count, errors_count, logs

def create_properties(rec, field_mapping):
    props = {}
    for notion_field, kintone_info in field_mapping.items():
        field_type = kintone_info["type"]
        kintone_field = kintone_info["field"]
        value = rec.get(kintone_field, {}).get("value", None)

        if value is None:
            continue

        try:
            if field_type == "title":
                props[notion_field] = {"title": [{"text": {"content": str(value)}}]}
            elif field_type == "rich_text":
                props[notion_field] = {"rich_text": [{"text": {"content": str(value)}}]}
            elif field_type == "number":
                props[notion_field] = {"number": float(value)}
            elif field_type == "date":
                if value:
                    props[notion_field] = {"date": {"start": value}}
        except Exception as e:
            print(f"プロパティ変換エラー ({notion_field}): {str(e)}")
    return props

# ---------------------------
# スクリプトA: kintone(App52)
# ---------------------------

def run_script_A(filter_date: str):
    print("\n===== スクリプトA処理開始 =====")
    k_token = os.environ.get("KINTONE_TOKEN_APP_52")
    if not k_token:
        return 0, 0, 0, ["Error: KINTONE_TOKEN_APP_52 not set"]

    field_mapping = {
        "レコード番号": {"type": "number", "field": "$id"},
        "取引先名": {"type": "title", "field": "取引先名"},
        "対応者": {"type": "rich_text", "field": "対応者"},
        "新規営業件名": {"type": "rich_text", "field": "新規営業件名"},
        "次回営業件名": {"type": "rich_text", "field": "次回営業件名"},
        "次回提案予定日": {"type": "date", "field": "次回提案予定日"},
        "対応日": {"type": "date", "field": "対応日"},
        "商談内容": {"type": "rich_text", "field": "商談内容"},
        "現在の課題・問題点": {"type": "rich_text", "field": "現在の課題・問題点"},
        "競合・マーケット情報": {"type": "rich_text", "field": "競合・マーケット情報"},
        "次回提案内容": {"type": "rich_text", "field": "次回提案内容"},
        "取引先ID": {"type": "number", "field": "取引先ID"}
    }

    return process_records(
        filter_date=filter_date,
        k_sub="n2amf",
        k_app="52",
        k_token=k_token,
        notion_db_id="1a74dbc3b61180ceb45ad2784be4d549",
        field_mapping=field_mapping
    )

# ---------------------------
# スクリプトB: kintone(App31)
# ---------------------------

def run_script_B(filter_date: str):
    print("\n===== スクリプトB処理開始 =====")
    k_token = os.environ.get("KINTONE_TOKEN_APP_31")
    if not k_token:
        return 0, 0, 0, ["Error: KINTONE_TOKEN_APP_31 not set"]

    field_mapping = {
        "レコード番号": {"type": "number", "field": "$id"},
        "取引先ID": {"type": "number", "field": "取引先ID"},
        "取引先名": {"type": "title", "field": "取引先名"},
        "営業担当": {"type": "rich_text", "field": "営業担当"},
        "都道府県": {"type": "rich_text", "field": "都道府県__隣に記載されている都道府県をコピペ"},
        "競争方法": {"type": "rich_text", "field": "競争方法"},
        "合意確定予測年度": {"type": "rich_text", "field": "合意確定予測年度"},
        "定員": {"type": "rich_text", "field": "定員"},
        "現委託先名": {"type": "rich_text", "field": "開園時預かり人数_0"},
        "確度": {"type": "rich_text", "field": "確度"},
        "予測利益額": {"type": "number", "field": "予測利益額"},
        "予測売上額": {"type": "number", "field": "予測売上額"},
        "商談開始日": {"type": "date", "field": "商談開始日"},
        "見積提出実施日": {"type": "date", "field": "見積提出実施日"},
        "公示日": {"type": "date", "field": "公示日"},
        "入札・プロポーザル日": {"type": "date", "field": "入札・プロポーザル参加日"},
        "合意・結果通知日": {"type": "date", "field": "合意日・結果通知日"},
        "開園日": {"type": "date", "field": "開園日"}
    }

    return process_records(
        filter_date=filter_date,
        k_sub="n2amf",
        k_app="31",
        k_token=k_token,
        notion_db_id="1ce4dbc3b61180c4899ecaa6feca4800",
        field_mapping=field_mapping
    )