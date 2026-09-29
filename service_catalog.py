"""Client for the shared, anonymous Google Apps Script service catalog."""
from __future__ import annotations
import re
import unicodedata
import requests

MAX_SERVICE_NAME = 200
MAX_LABEL_NAME = 80

class CatalogError(RuntimeError):
    pass

def _clean_text(value, limit, field):
    value = re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value or "")).strip())
    if not value or len(value) > limit or any(ord(c) < 32 for c in value):
        raise CatalogError(f"{field} không hợp lệ")
    return value

def service_key(value):
    return _clean_text(value, MAX_SERVICE_NAME, "Tên dịch vụ").casefold()

def validate_catalog(data):
    if not isinstance(data, dict) or data.get("ok") is not True:
        raise CatalogError(str(data.get("error", "API danh sách dịch vụ không hợp lệ") if isinstance(data, dict) else "API danh sách dịch vụ không hợp lệ"))
    services, labels, links = data.get("services"), data.get("labels"), data.get("links")
    if not all(isinstance(x, list) for x in (services, labels, links)):
        raise CatalogError("API danh sách dịch vụ thiếu dữ liệu")
    for row in services:
        if not isinstance(row, dict) or not row.get("service_id"):
            raise CatalogError("Dịch vụ sai cấu trúc")
        _clean_text(row.get("ten_dich_vu"), MAX_SERVICE_NAME, "Tên dịch vụ")
    for row in labels:
        if not isinstance(row, dict) or not row.get("label_id"):
            raise CatalogError("Nhãn sai cấu trúc")
        _clean_text(row.get("ten_nhan"), MAX_LABEL_NAME, "Tên nhãn")
    sids, lids = {str(x["service_id"]) for x in services}, {str(x["label_id"]) for x in labels}
    if any(not isinstance(x, dict) or str(x.get("service_id")) not in sids or str(x.get("label_id")) not in lids for x in links):
        raise CatalogError("Liên kết nhãn-dịch vụ sai cấu trúc")
    return {"ok": True, "services": services, "labels": labels, "links": links}

class ServiceCatalog:
    def __init__(self, endpoint, session=requests, timeout=15):
        self.endpoint, self.session, self.timeout = str(endpoint or "").strip(), session, timeout
    def _check_endpoint(self):
        if not self.endpoint.startswith("https://script.google.com/macros/s/") or not self.endpoint.endswith("/exec"):
            raise CatalogError("Chưa cấu hình Google Apps Script API dịch vụ")
    def get(self):
        self._check_endpoint()
        try:
            response = self.session.get(self.endpoint, timeout=self.timeout); response.raise_for_status()
            return validate_catalog(response.json())
        except CatalogError: raise
        except (requests.RequestException, ValueError) as exc: raise CatalogError("Không tải được danh mục dịch vụ online") from exc
    def post(self, payload):
        self._check_endpoint()
        try:
            response = self.session.post(self.endpoint, json=payload, timeout=self.timeout); response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or data.get("ok") is not True: raise CatalogError(str(data.get("error", "API từ chối cập nhật") if isinstance(data, dict) else "API từ chối cập nhật"))
            return data
        except CatalogError: raise
        except (requests.RequestException, ValueError) as exc: raise CatalogError("Không cập nhật được danh mục online") from exc
    def sync_services(self, names):
        names = list(dict.fromkeys(_clean_text(x, MAX_SERVICE_NAME, "Tên dịch vụ") for x in names))
        if not names: return []
        added = []
        for start in range(0, len(names), 100):
            batch = self.post({"action": "sync_services", "services": names[start:start + 100]}).get("added", [])
            if not isinstance(batch, list): raise CatalogError("API trả danh sách dịch vụ mới sai cấu trúc")
            added.extend(batch)
        return added
    def create_label(self, name): return self.post({"action": "create_label", "name": _clean_text(name, MAX_LABEL_NAME, "Tên nhãn")})
    def rename_label(self, label_id, name): return self.post({"action": "rename_label", "label_id": str(label_id), "name": _clean_text(name, MAX_LABEL_NAME, "Tên nhãn")})
    def delete_label(self, label_id): return self.post({"action": "delete_label", "label_id": str(label_id)})
    def set_label_services(self, label_id, service_ids): return self.post({"action": "set_label_services", "label_id": str(label_id), "service_ids": list(dict.fromkeys(map(str, service_ids)))[:100]})

def filter_selected_services(frame, service_ids, selected_label_ids, catalog):
    if frame.empty: return frame.copy()
    selected, labels = set(map(str, service_ids or [])), set(map(str, selected_label_ids or []))
    by_id = {str(x["service_id"]): x for x in catalog["services"]}
    selected.update(str(x["service_id"]) for x in catalog["links"] if str(x["label_id"]) in labels)
    names = {service_key(by_id[x]["ten_dich_vu"]) for x in selected if x in by_id}
    if "loaihinh_tb" not in frame.columns: raise CatalogError("Bảng OneBSS thiếu cột Loại hình thuê bao")
    if not names: return frame.iloc[0:0].copy()
    mask = frame["loaihinh_tb"].fillna("").map(lambda x: service_key(x) if str(x).strip() else "").isin(names)
    return frame.loc[mask].copy().reset_index(drop=True)
