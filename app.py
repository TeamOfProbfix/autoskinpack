from flask import Flask, request, send_file, render_template_string
import json, os, uuid, zipfile, io
from PIL import Image

app = Flask(__name__)

# --- CẤU HÌNH GIAO DIỆN ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skin Pack Generator Pro 🎭</title>
    <link rel="icon" type="image/png" href="/static/favicon.png">
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
            --glow-op: 0.5;
        }
        body.light-theme {
            --bg-grad: #f1f5f9; --card-bg: #ffffff; --text-main: #0f172a;
            --text-sub: #475569; --border: #e2e8f0; --input-bg: #f8fafc;
            --p-color: #4f46e5; --s-color: #0891b2; --glow-op: 0;
        }
        body.dark-theme {
            --bg-grad: #020617; --card-bg: #0f172a; --text-main: #f8fafc;
            --text-sub: #94a3b8; --border: #1e293b; --input-bg: #000000;
            --glow-op: 0;
        }

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

        .app { width: 100%; max-width: 500px; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h2 { font-size: 26px; background: linear-gradient(90deg, #fff, var(--s-color)); -webkit-background-clip: text; color: transparent; }

        .card { background: var(--card-bg); backdrop-filter: blur(15px); padding: 25px; border-radius: 24px; border: 1px solid var(--border); box-shadow: 0 20px 50px rgba(0,0,0,0.3); }

        .input-group { margin-bottom: 15px; }
        label { display: block; font-size: 11px; color: var(--text-sub); margin-bottom: 5px; font-weight: bold; text-transform: uppercase; }
        input, select { width: 100%; padding: 12px; border-radius: 12px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text-main); font-size: 14px; box-sizing: border-box; }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

        .drop-zone {
            border: 2px dashed var(--p-color); border-radius: 15px; padding: 20px; text-align: center;
            cursor: pointer; transition: 0.3s; background: rgba(0,0,0,0.2); margin-top: 10px;
        }
        .drop-zone:hover { border-color: var(--s-color); }

        .skin-list-container { margin-top: 20px; max-height: 300px; overflow-y: auto; }
        .skin-item {
            display: flex; align-items: center; gap: 12px; background: rgba(0,0,0,0.2);
            padding: 10px; border-radius: 12px; margin-bottom: 8px; border: 1px solid var(--border);
        }
        .skin-item img { width: 40px; height: 40px; border-radius: 5px; image-rendering: pixelated; }
        .skin-item input { padding: 8px; font-size: 13px; }

        .btn-main {
            width: 100%; padding: 15px; border: none; border-radius: 15px;
            background: linear-gradient(135deg, var(--p-color), var(--s-color));
            color: white; font-weight: bold; cursor: pointer; font-size: 16px; margin-top: 20px;
        }
        .btn-clear { background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 8px; cursor: pointer; font-size: 11px; float: right; margin-bottom: 10px;}

        .footer { text-align: center; margin-top: 30px; font-size: 11px; color: var(--text-sub); line-height: 1.8; }
        .footer a { color: var(--s-color); text-decoration: underline; font-weight: bold; }
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
    <div class="header"><h2>Skin Pack Generator ⚙️</h2></div>
    
    <div class="card">
        <div class="input-group">
            <label>Pack Name</label>
            <input type="text" id="packName" placeholder="My Skins">
        </div>

        <div class="input-group">
            <label>Description</label>
            <input type="text" id="packDesc" placeholder="A cool skin pack">
        </div>

        <div class="grid">
            <div class="input-group">
                <label>Version</label>
                <input type="text" id="packVer" value="1,0,0">
            </div>
            <div class="input-group">
                <label>Min Engine</label>
                <select id="minEngine">
                    <option value="1,26,3">1.26.3 (Latest)</option>
                    <option value="1,21,0">1.21.0</option>
                    <option value="1,20,0">1.20.0</option>
                </select>
            </div>
        </div>

        <div class="input-group">
            <label>Pack Icon (Optional)</label>
            <input type="file" id="iconInput" accept="image/png">
            <small style="font-size: 9px; color: var(--s-color)">*If empty, we'll use a skin's face!</small>
        </div>

        <div class="drop-zone" onclick="document.getElementById('fileInput').click()">
            <strong>Click to add Skins (.png)</strong>
            <input type="file" id="fileInput" multiple accept="image/png" style="display:none" onchange="handleFiles(this.files)">
        </div>

        <div class="skin-list-container">
            <button class="btn-clear" onclick="clearAll()">Clear All</button>
            <div id="skinList"></div>
        </div>

        <button class="btn-main" onclick="generatePack()">Generate .mcpack</button>
    </div>

    <div class="footer">
        <div>Made by <b>Probfix</b> & <b>AI partner</b> ⚡</div>
        <div>Make a manifest.json for Bedrock <a href="https://manifest-generator-y00b.onrender.com/" target="_blank">Here</a></div>
        <div>Make a pack.mcmeta for Java <a href="#" target="_blank">Here</a></div>
    </div>
</div>

<script>
    let selectedFiles = [];
    function toggleMenu() { document.getElementById('sidebar').classList.toggle('active'); }
    function setTheme(t) { document.body.className = t + '-theme'; toggleMenu(); }
    function clearAll() { selectedFiles = []; renderList(); }

    function handleFiles(files) {
        for (let file of files) {
            selectedFiles.push({ file: file, name: file.name.replace('.png', '') });
        }
        renderList();
    }

    function renderList() {
        const list = document.getElementById('skinList');
        list.innerHTML = '';
        selectedFiles.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'skin-item';
            div.innerHTML = `
                <img src="${URL.createObjectURL(item.file)}">
                <input type="text" value="${item.name}" oninput="selectedFiles[${index}].name = this.value">
                <button onclick="selectedFiles.splice(${index},1); renderList()" style="background:none; border:none; color:#ff4444; cursor:pointer">✕</button>
            `;
            list.appendChild(div);
        });
    }

    async function generatePack() {
        if (selectedFiles.length === 0) return alert("Please add skins!");
        const formData = new FormData();
        formData.append('packName', document.getElementById('packName').value || "MyPack");
        formData.append('packDesc', document.getElementById('packDesc').value || "Created with Probfix Tool");
        formData.append('packVer', document.getElementById('packVer').value);
        formData.append('minEngine', document.getElementById('minEngine').value);
        
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
</script>
</body>
</html>
'''

# --- BACKEND LOGIC ---

def get_skin_info(img_path):
    """Nhận diện loại tay và cắt mặt làm icon."""
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        # 1. Nhận diện tay (Slim vs Classic)
        geo = "geometry.humanoid.custom"
        if img.size == (64, 64):
            pixel = img.getpixel((54, 20))
            if pixel[3] == 0: geo = "geometry.humanoid.customSlim"
        
        # 2. Cắt khuôn mặt (Vùng mặt trước: x=8, y=8, w=8, h=8)
        face = img.crop((8, 8, 16, 16))
        face = face.resize((64, 64), Image.NEAREST)
        
        return geo, face

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate", methods=["POST"])
def generate():
    pack_name = request.form.get('packName', 'CustomPack')
    pack_desc = request.form.get('packDesc', '')
    version = [int(x) for x in request.form.get('packVer', '1,0,0').split(',')]
    engine = [int(x) for x in request.form.get('minEngine', '1,26,3').split(',')]
    count = int(request.form.get('count', 0))
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        skins_json = {"serialize_name": pack_name, "localization_name": pack_name, "skins": []}
        first_skin_face = None

        for i in range(count):
            file = request.files.get(f'skin_{i}')
            skin_name = request.form.get(f'name_{i}', f'Skin {i}')
            if file:
                temp_p = f"temp_{i}.png"
                file.save(temp_p)
                geo, face = get_skin_info(temp_p)
                
                # Lưu mặt của skin đầu tiên để làm icon dự phòng
                if i == 0: first_skin_face = face
                
                zf.write(temp_p, f"skin_{i}.png")
                skins_json["skins"].append({
                    "localization_name": skin_name,
                    "geometry": geo,
                    "texture": f"skin_{i}.png",
                    "type": "free"
                })
                os.remove(temp_p)

        # Xử lý Pack Icon
        custom_icon = request.files.get('customIcon')
        if custom_icon:
            zf.writestr("pack_icon.png", custom_icon.read())
        elif first_skin_face:
            img_byte_arr = io.BytesIO()
            first_skin_face.save(img_byte_arr, format='PNG')
            zf.writestr("pack_icon.png", img_byte_arr.getvalue())

        # Ghi các file hệ thống
        zf.writestr("skins.json", json.dumps(skins_json, indent=4))
        manifest = {
            "format_version": 2,
            "header": {
                "name": pack_name, "description": pack_desc,
                "uuid": str(uuid.uuid4()), "version": version, "min_engine_version": engine
            },
            "modules": [{"type": "skin_pack", "uuid": str(uuid.uuid4()), "version": version}]
        }
        zf.writestr("manifest.json", json.dumps(manifest, indent=4))
        zf.writestr("texts/en_US.lang", f"skinpack.{pack_name}={pack_name}")

    memory_file.seek(0)
    return send_file(memory_file, download_name=f"{pack_name}.mcpack", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
