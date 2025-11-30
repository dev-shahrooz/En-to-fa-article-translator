// Basic front-end hook to prevent full page reload for demo upload.
document.getElementById('upload-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const response = await fetch(form.action, { method: 'POST', body: formData });
  const payload = await response.json();
  alert(`Stub response: Job ${payload.job_id} is ${payload.status}.`);
});
