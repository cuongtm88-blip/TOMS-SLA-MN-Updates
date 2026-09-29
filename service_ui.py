"""Shared service filter dialog (local choices, online shared labels)."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import service_catalog

def open_service_window(parent, client, settings, on_save):
    try:
        catalog = client.get()
    except service_catalog.CatalogError as exc:
        messagebox.showerror("Dịch vụ", str(exc), parent=parent); return
    win = tk.Toplevel(parent); win.title("Dịch vụ và nhãn"); win.geometry("760x520")
    tabs = ttk.Notebook(win); tabs.pack(fill="both", expand=True, padx=8, pady=8)
    filt, manage = ttk.Frame(tabs, padding=8), ttk.Frame(tabs, padding=8)
    tabs.add(filt, text="Lọc dịch vụ (riêng máy này)"); tabs.add(manage, text="Quản lý nhãn (dùng chung)")
    mode = tk.StringVar(value=settings.get("service_filter_mode", "all"))
    ttk.Radiobutton(filt, text="Tất cả dịch vụ", variable=mode, value="all").pack(anchor="w")
    ttk.Radiobutton(filt, text="Chỉ dịch vụ/nhãn đã chọn", variable=mode, value="custom").pack(anchor="w")
    ttk.Label(filt, text="Dịch vụ được tô sáng gồm dịch vụ chọn trực tiếp và dịch vụ thuộc nhãn đang chọn.").pack(anchor="w")
    panes = ttk.Frame(filt); panes.pack(fill="both", expand=True, pady=6)
    service_box = ttk.LabelFrame(panes, text="Dịch vụ"); label_box = ttk.LabelFrame(panes, text="Nhãn")
    service_box.pack(side="left", fill="both", expand=True, padx=4); label_box.pack(side="left", fill="both", expand=True, padx=4)
    svc = tk.Listbox(service_box, selectmode="multiple", exportselection=False); lab = tk.Listbox(label_box, selectmode="multiple", exportselection=False)
    svc_scroll = ttk.Scrollbar(service_box, orient="vertical", command=svc.yview); lab_scroll = ttk.Scrollbar(label_box, orient="vertical", command=lab.yview)
    svc.configure(yscrollcommand=svc_scroll.set); lab.configure(yscrollcommand=lab_scroll.set)
    svc.pack(side="left", fill="both", expand=True); svc_scroll.pack(side="right", fill="y")
    lab.pack(side="left", fill="both", expand=True); lab_scroll.pack(side="right", fill="y")
    sids = [str(x["service_id"]) for x in catalog["services"]]; lids = [str(x["label_id"]) for x in catalog["labels"]]
    links = {}
    for x in catalog["links"]: links.setdefault(str(x["label_id"]), set()).add(str(x["service_id"]))
    for x in catalog["services"]: svc.insert("end", x["ten_dich_vu"])
    for x in catalog["labels"]: lab.insert("end", x["ten_nhan"])
    saved = settings.get("selected_service_ids")
    direct_service_ids = set(map(str, saved or []))
    if mode.get() == "all" and saved is None: direct_service_ids = set(sids)
    for i, ident in enumerate(lids):
        if ident in set(map(str, settings.get("selected_service_label_ids", []))): lab.select_set(i)
    displayed_service_ids = set(); selection_syncing = {"active": False}
    def selected_filter_labels(): return {lids[i] for i in lab.curselection()}
    def filter_label_service_ids():
        chosen = selected_filter_labels()
        return set().union(*(links.get(ident, set()) for ident in chosen)) if chosen else set()
    def refresh_filter_marks():
        selection_syncing["active"] = True
        visible = direct_service_ids | filter_label_service_ids()
        svc.selection_clear(0, "end")
        for i, ident in enumerate(sids):
            if ident in visible: svc.selection_set(i)
        displayed_service_ids.clear(); displayed_service_ids.update(visible)
        selection_syncing["active"] = False
    def service_selection_changed(_event=None):
        if selection_syncing["active"]: return
        current = {sids[i] for i in svc.curselection()}
        direct_service_ids.update(current - displayed_service_ids)
        direct_service_ids.difference_update((displayed_service_ids - current) - filter_label_service_ids())
        refresh_filter_marks()
    svc.bind("<<ListboxSelect>>", service_selection_changed)
    lab.bind("<<ListboxSelect>>", lambda _event: refresh_filter_marks())
    refresh_filter_marks()
    ttk.Label(manage, text="Nhãn và thành viên được chia sẻ cho mọi máy.").pack(anchor="w")
    group = ttk.LabelFrame(manage, text="Dịch vụ thuộc nhãn"); group.pack(fill="both", expand=True, pady=8)
    lb = tk.Listbox(group, exportselection=False, width=25); mb = tk.Listbox(group, selectmode="multiple", exportselection=False)
    lb.pack(side="left", fill="y", padx=4, pady=4); lb_scroll = ttk.Scrollbar(group, orient="vertical", command=lb.yview); lb.configure(yscrollcommand=lb_scroll.set); lb_scroll.pack(side="left", fill="y")
    mb_scroll = ttk.Scrollbar(group, orient="vertical", command=mb.yview); mb.configure(yscrollcommand=mb_scroll.set)
    mb.pack(side="left", fill="both", expand=True, padx=4, pady=4); mb_scroll.pack(side="right", fill="y")
    def refresh():
        nonlocal catalog, sids, lids, links
        keep_labels = selected_filter_labels()
        catalog = client.get(); sids = [str(x["service_id"]) for x in catalog["services"]]; lids = [str(x["label_id"]) for x in catalog["labels"]]; links = {}
        for x in catalog["links"]: links.setdefault(str(x["label_id"]), set()).add(str(x["service_id"]))
        for w in (lb, mb, svc, lab): w.delete(0, "end")
        for x in catalog["labels"]: lb.insert("end", x["ten_nhan"]); lab.insert("end", x["ten_nhan"])
        for x in catalog["services"]: mb.insert("end", x["ten_dich_vu"]); svc.insert("end", x["ten_dich_vu"])
        direct_service_ids.intersection_update(sids)
        for i, ident in enumerate(lids):
            if ident in keep_labels: lab.select_set(i)
        refresh_filter_marks()
    def show_members(_=None):
        mb.selection_clear(0, "end"); sel = lb.curselection()
        if sel:
            for i, ident in enumerate(sids):
                if ident in links.get(lids[sel[0]], set()): mb.selection_set(i)
    lb.bind("<<ListboxSelect>>", show_members)
    def invoke(fn, *args):
        try: fn(*args); refresh()
        except service_catalog.CatalogError as exc: messagebox.showerror("Dịch vụ", str(exc), parent=win)
    def create():
        name = simpledialog.askstring("Tạo nhãn", "Tên nhãn mới:", parent=win)
        if name: invoke(client.create_label, name)
    def rename():
        sel = lb.curselection()
        if not sel: return messagebox.showwarning("Đổi tên", "Hãy chọn nhãn.", parent=win)
        name = simpledialog.askstring("Đổi tên nhãn", "Tên mới:", initialvalue=lb.get(sel[0]), parent=win)
        if name: invoke(client.rename_label, lids[sel[0]], name)
    def delete():
        sel = lb.curselection()
        if sel and messagebox.askyesno("Xóa nhãn", "Xóa nhãn này và liên kết?", parent=win): invoke(client.delete_label, lids[sel[0]])
    def members():
        sel = lb.curselection()
        if not sel: return messagebox.showwarning("Nhãn", "Hãy chọn nhãn.", parent=win)
        invoke(client.set_label_services, lids[sel[0]], [sids[i] for i in mb.curselection()])
    actions = ttk.Frame(manage); actions.pack(fill="x", pady=4)
    for text, fn in (("Tạo nhãn", create), ("Đổi tên", rename), ("Xóa nhãn", delete), ("Lưu thành viên", members)): ttk.Button(actions, text=text, command=fn).pack(side="left", padx=3)
    def save():
        on_save({"service_filter_mode": mode.get(), "selected_service_ids": [ident for ident in sids if ident in direct_service_ids], "selected_service_label_ids": [lids[i] for i in lab.curselection()]}); win.destroy()
    ttk.Button(win, text="Lưu lựa chọn trên máy này", command=save).pack(anchor="e", padx=12, pady=8)
