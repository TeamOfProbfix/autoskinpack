from flask import Flask, request, send_file, render_template_string
import json, os, uuid, zipfile, io
from PIL import Image

app = Flask(__name__)

# --- UI TEMPLATE ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skin Pack Generator Pro ⚙️</title>
    <style>
        :root {
            --bg-grad: radial-gradient(circle at top, #1e1b4b, #020617);
            --card-bg: rgba(30, 41, 59, 0.8);
            --text-main: #ffffff;
            --text-sub: #a5b4fc;
            --border: rgba(255,255,255,0.1);
            --input-bg: #020617;
            --p-color: #7c3aed;
            --s-color: #22d3ee;
        }
        body.light-theme { --bg-grad: #f1f5f9; --card-bg: #ffffff; --text-main: #0f172a; --text-sub: #475569; --border: #e2e8f0; --input-bg: #f8fafc; --p-color: #4f46e5; --s-color: #0891b2; }
        body.dark-theme { --bg-grad: #020617; --card-bg: #0f172a; --text-main: #f8fafc; --text-sub: #94a3b8; --border: #1e293b; --input-bg: #000000; }

        body { 
            margin: 0; font-family: 'Segoe UI', sans-serif; 
            background: var(--bg-grad); color: var(--text-main);
            min-height: 100vh; display: flex; justify-content: center; transition: 0.3s;
        }

        .menu-btn { position: fixed; top: 20px; right: 20px; cursor: pointer; z-index: 100; padding: 10px; background: var(--card-bg); border-radius: 10px; border: 1px solid var(--border); }
        .menu-btn div { width: 25px; height: 3px; background: var(--s-color); margin: 5px 0; border-radius: 2px; }
        .sidebar { position: fixed; top: 0; right: -250px; width: 200px; height: 100%; background: var(--card-bg); backdrop-filter: blur(20px); padding: 60px 20px; transition: 0.4s; z-index: 90; border-left: 1px solid var(--border); }
        .sidebar.active { right: 0; }
        .theme-opt { display: block; width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text-main); border-radius: 10px; cursor: pointer; text-align: left; }

        .app { width: 100%; max-width: 550px; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h2 { font-size: 28px; margin-bottom: 5px; background: linear-gradient(90deg, #fff, var(--s-color)); -webkit-background-clip: text; color: transparent; }
        .header p { font-size: 12px; color: var(--text-sub); margin: 0; opacity: 0.8; }

        .card { background: var(--card-bg); backdrop-filter: blur(15px); padding: 25px; border-radius: 24px; border: 1px solid var(--border); box-shadow: 0 20px 50px rgba(0,0,0,0.3); margin-bottom: 20px; }

        .input-group { margin-bottom: 15px; }
        label { display: block; font-size: 10px; color: var(--text-sub); margin-bottom: 5px; font-weight: bold; text-transform: uppercase; }
        input, select { width: 100%; padding: 12px; border-radius: 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text-main); font-size: 14px; box-sizing: border-box; }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

        .drop-zone {
            border: 2px dashed var(--p-color); border-radius: 15px; padding: 20px; text-align: center;
            cursor: pointer; transition: 0.3s; background: rgba(0,0,0,0.2);
        }
        .drop-zone:hover { border-color: var(--s-color); background: rgba(34, 211, 238, 0.05); }

        .skin-item {
            display: flex; align-items: center; gap: 12px; background: rgba(255,255,255,0.03);
            padding: 10px; border-radius: 12px; margin-bottom: 8px; border: 1px solid var(--border);
        }
        .skin-item img { width: 40px; height: 40px; border-radius: 5px; image-rendering: pixelated; background: #222; }
        .skin-item input { flex: 1; padding: 8px; font-size: 13px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); }

        .btn-group { display: flex; gap: 8px; margin-top: 10px; }
        .btn-small { flex: 1; padding: 10px; font-size: 11px; border-radius: 10px; border: 1px solid var(--border); background: var(--card-bg); color: white; cursor: pointer; transition: 0.2s; }
        .btn-small:hover { background: var(--s-color); color: black; }
        
        .btn-main {
            width: 100%; padding: 16px; border: none; border-radius: 15px;
            background: linear-gradient(135deg, var(--p-color), var(--s-color));
            color: white; font-weight: bold; cursor: pointer; font-size: 16px; margin-top: 10px;
        }

        .code-preview { background: #000; padding: 15px; border-radius: 12px; font-size: 11px; color: #38bdf8; overflow: auto; max-height: 200px; border: 1px solid var(--border); display: none; margin-top: 10px; }
        pre { margin: 0; white-space: pre-wrap; word-wrap: break-word; }

        .footer { text-align: center; margin-top: 30px; font-size: 11px; color: var(--text-sub); line-height: 1.8; }
        .footer b { color: var(--s-color); }
        .footer a { color: var(--s-color); font-weight: bold; text-decoration: underline; }
        
        .control-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; margin-top: 20px; }
        .badge { background: var(--p-color); padding: 2px 8px; border-radius: 5px; font-size: 9px; }
    </style>
</head>
<body class="neon-theme">

<div class="menu-btn" onclick="toggleMenu()"><div></div><div></div><div></div></div>
<div class="sidebar" id="sidebar">
    <h4>Select Theme</h4>
    <button class="theme-opt" onclick="setTheme('neon')">✨ Neon Mode</button>
    <button class="theme-opt" onclick="setTheme('dark')">🌙 Dark Mode</button>
    <button class="theme-opt" onclick="setTheme('light')">☀️ Light Mode</button>
</div>

<div class="app">
    <div class="header">
        <h2>Skin Pack Generator ⚙️</h2>
        <p>Web có thể sai, vui lòng thông cảm</p>
    </div>
    
    <div class="card">
        <div class="grid">
            <div class="input-group">
                <label>Pack Name</label>
                <input type="text" id="packName" placeholder="My Skins" oninput="updateManifest()">
            </div>
            <div class="input-group">
                <label>Version</label>
                <input type="text" id="packVer" value="1,0,0" oninput="updateManifest()">
            </div>
        </div>

        <div class="input-group">
            <label>Description</label>
            <input type="text" id="packDesc" placeholder="Enter pack description..." oninput="updateManifest()">
        </div>

        <div class="input-group">
            <label>Min Engine Version</label>
            <select id="minEngine" onchange="updateManifest()">
                <option value="1,26,3">1.26.3</option>
                <option value="1,21,0">1.21.0</option>
                <option value="1,17,0">1.17.0</option>
            </select>
        </div>

        <div class="input-group">
            <label>Pack Icon (Optional)</label>
            <input type="file" id="iconInput" accept="image/png">
        </div>

        <label>Skins Management</label>
        <div class="drop-zone" onclick="document.getElementById('fileInput').click()">
            <strong>Click or Drop Skin Images</strong>
            <input type="file" id="fileInput" multiple accept="image/png" style="display:none" onchange="handleFiles(this.files)">
        </div>
        
        <button class="btn-small" style="width:auto; margin-top:10px; font-size:9px;" onclick="toggleView('skinsCode')">Show Skins.json Preview</button>
        <div id="skinsCode" class="code-preview"><pre id="skinsJsonText"></pre></div>

        <div class="control-header">
            <span class="badge">Skin List</span>
            <div>
                <button class="btn-small" style="color:#facc15" onclick="restoreSkins()">Restore</button>
                <button class="btn-small" style="color:#ef4444" onclick="clearSkins()">Clear All</button>
            </div>
        </div>
        <div id="skinList"></div>
    </div>

    <div class="card">
        <label>Manifest.json Preview</label>
        <div id="manifestCode" class="code-preview" style="display:block;"><pre id="manifestText"></pre></div>
        
        <div class="btn-group">
            <button class="btn-small" onclick="generatePack()">Download .mcpack</button>
            <button class="btn-small" onclick="copyText('manifestText')">Copy JSON</button>
            <button class="btn-small" onclick="randomizeUUIDs()">Random UUIDs</button>
            <button class="btn-small" onclick="copyUUIDs()">Copy UUIDs</button>
        </div>
        <button class="btn-main" onclick="generatePack()">Download Final Pack 🚀</button>
    </div>

    <div class="footer">
        <div>Made by <b>Probfix</b> & <b>AI partner⚡</b></div>
        <div>Need a Manifest? <a href="https://mc-manifestgenerator.onrender.com" target="_blank">Manifest Generator ⚙️</a></div>
        <div>Java Developer? <a href="#" target="_blank">Make a pack.mcmeta for Java here</a></div>
    </div>
</div>

<script>
    let selectedFiles = [];
    let backupFiles = [];
    let u1 = genUUID(), u2 = genUUID();

    function genUUID() { return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random()*16|0; return (c=='x'?r:(r&0x3|0x8)).toString(16); }); }
    function toggleMenu() { document.getElementById('sidebar').classList.toggle('active'); }
    function setTheme(t) { document.body.className = t + '-theme'; toggleMenu(); }
    function toggleView(id) { const el = document.getElementById(id); el.style.display = el.style.display === 'none' ? 'block' : 'none'; }

    function handleFiles(files) {
        for (let file of files) {
            selectedFiles.push({ file: file, name: file.name.replace('.png', ''), url: URL.createObjectURL(file) });
        }
        renderList();
    }

    function clearSkins() { backupFiles = [...selectedFiles]; selectedFiles = []; renderList(); }
    function restoreSkins() { if(backupFiles.length > 0) { selectedFiles = [...backupFiles]; renderList(); } }

    function renderList() {
        const list = document.getElementById('skinList');
        list.innerHTML = '';
        selectedFiles.forEach((item, i) => {
            const div = document.createElement('div');
            div.className = 'skin-item';
            div.innerHTML = `
                <img src="${item.url}">
                <input type="text" value="${item.name}" oninput="selectedFiles[${i}].name = this.value; updateSkinsJson()">
                <button onclick="selectedFiles.splice(${i},1); renderList()" style="background:none; border:none; color:#ff4444; cursor:pointer">✕</button>
            `;
            list.appendChild(div);
        });
        updateSkinsJson();
        updateManifest();
    }

    function updateSkinsJson() {
        const data = {
            serialize_name: document.getElementById('packName').value || "Pack",
            localization_name: document.getElementById('packName').value || "Pack",
            skins: selectedFiles.map((s, i) => ({
                localization_name: s.name,
                geometry: "geometry.humanoid.custom",
                texture: `skin_${i}.png`,
                type: "free"
            }))
        };
        document.getElementById('skinsJsonText').innerText = JSON.stringify(data, null, 4);
    }

    function updateManifest() {
        const name = document.getElementById('packName').value || "My Pack";
        const desc = document.getElementById('packDesc').value || "Skin pack";
        const ver = document.getElementById('packVer').value.split(',').map(Number);
        const engine = document.getElementById('minEngine').value.split(',').map(Number);
        
        const manifest = {
            format_version: 2,
            header: { name, description: desc, uuid: u1, version: ver, min_engine_version: engine },
            modules: [{ type: "skin_pack", uuid: u2, version: ver }]
        };
        document.getElementById('manifestText').innerText = JSON.stringify(manifest, null, 4);
    }

    function randomizeUUIDs() { u1 = genUUID(); u2 = genUUID(); updateManifest(); }
    function copyUUIDs() { navigator.clipboard.writeText(`Header: ${u1}\\nModule: ${u2}`); alert("UUIDs Copied!"); }
    function copyText(id) { navigator.clipboard.writeText(document.getElementById(id).innerText); alert("JSON Copied!"); }

    async function generatePack() {
        if (selectedFiles.length === 0) return alert("Please add skins!");
        const formData = new FormData();
        formData.append('packName', document.getElementById('packName').value || "MyPack");
        formData.append('packDesc', document.getElementById('packDesc').value || "");
        formData.append('packVer', document.getElementById('packVer').value);
        formData.append('minEngine', document.getElementById('minEngine').value);
        formData.append('u1', u1); formData.append('u2', u2);
        
        const iconFile = document.getElementById('iconInput').files[0];
        if(iconFile) formData.append('customIcon', iconFile);

        selectedFiles.forEach((item, i) => {
            formData.append(`skin_${i}`, item.file);
            formData.append(`name_${i}`, item.name);
        });
        formData.append('count', selectedFiles.length);

        const res = await fetch('/generate', { method: 'POST', body: formData });
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `${document.getElementById('packName').value || 'Skins'}.mcpack`;
        a.click();
    }
    
    updateManifest();
</script>
</body>
</html>
'''

# --- BACKEND ---
def get_skin_info(img_path):
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        geo = "geometry.humanoid.custom"
        if img.size == (64, 64):
            pixel = img.getpixel((54, 20))
            if pixel[3] == 0: geo = "geometry.humanoid.customSlim"
        face = img.crop((8, 8, 16, 16)).resize((64, 64), Image.NEAREST)
        return geo, face

@app.route("/")
def index(): return render_template_string(HTML_TEMPLATE)

@app.route("/generate", methods=["POST"])
def generate():
    name = request.form.get('packName', 'Pack')
    desc = request.form.get('packDesc', '')
    ver = [int(x) for x in request.form.get('packVer', '1,0,0').split(',')]
    eng = [int(x) for x in request.form.get('minEngine', '1,26,3').split(',')]
    u1, u2 = request.form.get('u1'), request.form.get('u2')
    count = int(request.form.get('count', 0))
    
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        sj = {"serialize_name": name, "localization_name": name, "skins": []}
        first_face = None
        for i in range(count):
            f = request.files.get(f'skin_{i}')
            sname = request.form.get(f'name_{i}', f'Skin {i}')
            if f:
                path = f"t_{i}.png"
                f.save(path)
                geo, face = get_skin_info(path)
                if i == 0: first_face = face
                zf.write(path, f"skin_{i}.png")
                sj["skins"].append({"localization_name": sname, "geometry": geo, "texture": f"skin_{i}.png", "type": "free"})
                os.remove(path)
        
        cicon = request.files.get('customIcon')
        if cicon: zf.writestr("pack_icon.png", cicon.read())
        elif first_face:
            b = io.BytesIO(); first_face.save(b, 'PNG')
            zf.writestr("pack_icon.png", b.getvalue())

        zf.writestr("skins.json", json.dumps(sj, indent=4))
        mani = {"format_version": 2, "header": {"name": name, "description": desc, "uuid": u1, "version": ver, "min_engine_version": eng}, "modules": [{"type": "skin_pack", "uuid": u2, "version": ver}]}
        zf.writestr("manifest.json", json.dumps(mani, indent=4))
        zf.writestr("texts/en_US.lang", f"skinpack.{name}={name}")
    mem.seek(0)
    return send_file(mem, download_name=f"{name}.mcpack", as_attachment=True)

if __name__ == "__main__": app.run(debug=True)
