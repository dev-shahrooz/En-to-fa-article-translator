// Simple dashboard interactions for the PDF Article Translator (NLLB)
// Handles uploads, job listing, and periodic status polling.

const uploadForm = document.getElementById('upload-form');
const uploadStatusEl = document.getElementById('upload-status');
const jobsBody = document.getElementById('jobs-body');
const pollingIndicator = document.getElementById('polling-indicator');

// Track jobs in memory so we can poll them periodically.
const jobs = new Map(); // jobId -> { id, filename, status }
const POLL_INTERVAL_MS = 5000;
let pollerId = null;

/**
 * Render a job row in the table. Creates a new row if missing or updates existing.
 */
function renderJob(job) {
  let row = document.querySelector(`[data-job-id="${job.id}"]`);

  // Remove placeholder row when the first job is added.
  const emptyRow = jobsBody.querySelector('.empty-row');
  if (emptyRow) {
    emptyRow.remove();
  }

  if (!row) {
    row = document.createElement('tr');
    row.setAttribute('data-job-id', job.id);
    row.innerHTML = `
      <td class="job-id">${job.id}</td>
      <td class="job-name"></td>
      <td class="job-status"></td>
      <td class="job-download"></td>
    `;
    jobsBody.prepend(row);
  }

  row.querySelector('.job-name').textContent = job.filename || '—';
  row.querySelector('.job-status').innerHTML = renderStatusBadge(job.status);
  row.querySelector('.job-download').innerHTML = renderDownloadLink(job);
}

/**
 * Convert a job status into a badge element.
 */
function renderStatusBadge(status = 'pending') {
  const normalized = status.toLowerCase();
  return `<span class="badge ${normalized}">${status}</span>`;
}

/**
 * Render the download link if the job is ready.
 */
function renderDownloadLink(job) {
  if (job.status && job.status.toLowerCase() === 'done') {
    return `<a href="/api/download/${encodeURIComponent(job.id)}" download>Download</a>`;
  }
  return '<span class="link-disabled">Not ready</span>';
}

/**
 * Start polling the status endpoint for all known jobs.
 */
function startPolling() {
  if (pollerId !== null || jobs.size === 0) return;
  pollerId = window.setInterval(pollAllJobs, POLL_INTERVAL_MS);
}

/**
 * Poll status for each known job and update the table.
 */
async function pollAllJobs() {
  if (jobs.size === 0) return;
  if (pollingIndicator) {
    pollingIndicator.textContent = 'Refreshing…';
  }

  const updates = Array.from(jobs.values()).map(async (job) => {
    try {
      const res = await fetch(`/api/status/${encodeURIComponent(job.id)}`);
      if (!res.ok) throw new Error(`Status request failed (${res.status})`);
      const payload = await res.json();
      const updated = {
        id: job.id,
        filename: payload.filename || job.filename,
        status: payload.status || job.status,
      };
      jobs.set(job.id, updated);
      renderJob(updated);
    } catch (error) {
      console.error('Failed to poll job status', error);
    }
  });

  await Promise.all(updates);
  if (pollingIndicator) {
    pollingIndicator.textContent = 'Auto-refreshing…';
  }
}

/**
 * Handle upload form submission using fetch + FormData.
 */
async function handleUpload(event) {
  event.preventDefault();
  if (!uploadForm) return;

  const submitButton = uploadForm.querySelector('button[type="submit"]');
  if (submitButton) submitButton.disabled = true;
  uploadStatusEl.textContent = 'Uploading…';

  try {
    const formData = new FormData(uploadForm);
    const response = await fetch(uploadForm.action, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed (${response.status})`);
    }

    const payload = await response.json();
    const job = {
      id: payload.job_id || payload.id,
      filename: payload.filename || formData.get('file')?.name || 'PDF',
      status: payload.status || 'pending',
    };

    if (!job.id) throw new Error('Missing job id in response');

    jobs.set(job.id, job);
    renderJob(job);
    startPolling();

    uploadStatusEl.textContent = 'Upload successful! Job created.';
    uploadForm.reset();
  } catch (error) {
    console.error(error);
    uploadStatusEl.textContent = `Error: ${error.message}`;
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

// Initialize listeners.
if (uploadForm) {
  uploadForm.addEventListener('submit', handleUpload);
}

// If the page renders with pre-existing rows (server-side), seed them for polling.
function seedExistingJobs() {
  const existingRows = jobsBody?.querySelectorAll('tr[data-job-id]') || [];
  existingRows.forEach((row) => {
    const id = row.getAttribute('data-job-id');
    const filename = row.querySelector('.job-name')?.textContent?.trim();
    const status = row.querySelector('.job-status')?.textContent?.trim();
    if (id) {
      jobs.set(id, { id, filename, status });
    }
  });
  if (jobs.size > 0) startPolling();
}

seedExistingJobs();
