import API from "../api.js";
import { toast, escapeHtml } from "../helpers.js";

let fileToken = null;
let excelColumns = [];
let entityType = "buyer";

export default {
  key: "import",
  label: "📥 Excel İçe Aktar",
  adminOnly: true,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Excel İçe Aktarma</div>
      <div class="page-hint">1) Dosya seçin → 2) Alan eşleştirmesi yapın → 3) İçe aktarın. Desteklenen format: .xlsx</div>

      <div class="card">
        <h3>Ne içe aktarılıyor?</h3>
        <div class="checkbox-row" style="gap:20px;">
          <label><input type="radio" name="entity-type" value="buyer" checked> Hosted Buyer</label>
          <label><input type="radio" name="entity-type" value="participant"> Katılımcı Firma</label>
        </div>
      </div>

      <div class="card">
        <h3>Dosya Seç</h3>
        <input type="file" id="file-input" accept=".xlsx">
        <div id="file-name" style="margin-top:8px; color:var(--ash); font-size:12px;"></div>
      </div>

      <div class="card" id="mapping-card" style="display:none;">
        <h3>Alan Eşleştirme</h3>
        <div id="mapping-fields"></div>
      </div>

      <div class="card" id="preview-card" style="display:none;">
        <h3>Önizleme (ilk 5 satır)</h3>
        <div class="table-wrap"><table id="preview-table"></table></div>
      </div>

      <button class="btn primary" id="import-btn" disabled>İçe Aktar</button>
      <div id="import-result" style="margin-top:14px;"></div>
    `;

    fileToken = null;
    excelColumns = [];
    entityType = "buyer";

    container.querySelectorAll('input[name="entity-type"]').forEach(radio => {
      radio.addEventListener("change", async (e) => {
        entityType = e.target.value;
        if (excelColumns.length) await this.buildMappingForm(container);
      });
    });

    container.querySelector("#file-input").addEventListener("change", (e) => this.onFileSelected(container, e));
    container.querySelector("#import-btn").addEventListener("click", () => this.doImport(container, state));
  },

  async onFileSelected(container, e) {
    const file = e.target.files[0];
    if (!file) return;
    container.querySelector("#file-name").textContent = file.name;

    let result;
    try {
      result = await API.uploadFile(file);
    } catch (err) {
      toast("Yükleme hatası: " + err.message, "error");
      return;
    }

    fileToken = result.file_token;
    excelColumns = result.columns;

    const previewTable = container.querySelector("#preview-table");
    previewTable.innerHTML =
      "<thead><tr>" + excelColumns.map(c => `<th>${escapeHtml(c)}</th>`).join("") + "</tr></thead>" +
      "<tbody>" + result.preview_rows.map(row =>
        "<tr>" + row.map(v => `<td>${escapeHtml(v)}</td>`).join("") + "</tr>"
      ).join("") + "</tbody>";
    container.querySelector("#preview-card").style.display = "block";

    await this.buildMappingForm(container);
    container.querySelector("#import-btn").disabled = false;
  },

  async buildMappingForm(container) {
    let fields;
    try {
      fields = await API.importFields(entityType);
    } catch (e) {
      toast("Alanlar alınamadı: " + e.message, "error");
      return;
    }

    const mappingCard = container.querySelector("#mapping-card");
    const mappingFields = container.querySelector("#mapping-fields");
    mappingCard.style.display = "block";

    mappingFields.innerHTML = fields.map(f => {
      // basit otomatik eşleştirme önerisi
      let autoIndex = -1;
      excelColumns.forEach((col, idx) => {
        if (autoIndex === -1 && col.toLowerCase().includes(f.label.split(" ")[0].toLowerCase())) {
          autoIndex = idx;
        }
      });
      const options = ['<option value="">(Eşleştirme yok)</option>']
        .concat(excelColumns.map((col, idx) =>
          `<option value="${escapeHtml(col)}" ${idx === autoIndex ? "selected" : ""}>${escapeHtml(col)}</option>`));
      return `
        <div class="form-field" style="margin-bottom:10px;">
          <label>${escapeHtml(f.label)}</label>
          <select data-field="${f.field}">${options.join("")}</select>
        </div>
      `;
    }).join("");
  },

  async doImport(container, state) {
    if (!state.eventId) { toast("Önce bir etkinlik seçin.", "error"); return; }
    if (!fileToken) { toast("Önce bir Excel dosyası seçin.", "error"); return; }

    const mapping = {};
    container.querySelectorAll("#mapping-fields select").forEach(sel => {
      if (sel.value) mapping[sel.dataset.field] = sel.value;
    });

    let result;
    try {
      result = await API.commitImport({
        event_id: state.eventId, entity_type: entityType, file_token: fileToken, mapping,
      });
    } catch (e) {
      toast("İçe aktarma hatası: " + e.message, "error");
      return;
    }

    let msg = `${result.created} / ${result.total_rows} kayıt içe aktarıldı.`;
    if (result.errors.length) {
      msg += "<br><br>Hatalar:<br>" + result.errors.slice(0, 10).map(escapeHtml).join("<br>");
    }
    container.querySelector("#import-result").innerHTML = `<div class="card">${msg}</div>`;
    toast("İçe aktarma tamamlandı.", "success");
  },
};
