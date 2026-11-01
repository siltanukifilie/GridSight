/* Public hosting has no operator authentication. Keep batch uploads local. */
(() => {
  if (document.body.dataset.publicDemo !== 'true') return;
  const ids = ['validation-form', 'monthly-validation-form', 'confidence-study-form', 'update-form'];
  const protect = () => {
    for (const id of ids) {
      const form = document.getElementById(id);
      if (!form || form.dataset.publicLocked) continue;
      form.dataset.publicLocked = 'true';
      const notice = document.createElement('p');
      notice.className = 'deployment-notice';
      notice.textContent = 'Local validation only. Meter uploads are disabled on this public demo. Download the templates and run GridSight locally with approved data.';
      const fieldset = document.createElement('fieldset');
      fieldset.disabled = true;
      fieldset.className = 'public-upload-disabled';
      while (form.firstChild) fieldset.appendChild(form.firstChild);
      form.append(notice, fieldset);
      form.addEventListener('submit', event => event.preventDefault(), {capture: true});
    }
  };
  new MutationObserver(protect).observe(document.getElementById('view-evidence'), {childList: true, subtree: true});
  protect();
})();
