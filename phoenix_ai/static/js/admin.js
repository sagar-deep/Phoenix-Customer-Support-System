/* ============================================================
   Phoenix AI – Admin JavaScript
   ============================================================ */

async function closeTicket(id) {
  if (!confirm('Mark this ticket as Closed?')) return;
  const res = await fetch(`/api/complaint/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Closed' })
  });
  if ((await res.json()).success) location.reload();
}

async function reopenTicket(id) {
  if (!confirm('Re-open this ticket?')) return;
  const res = await fetch(`/api/complaint/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Open' })
  });
  if ((await res.json()).success) location.reload();
}

async function deleteTicket(id) {
  if (!confirm('Permanently delete this complaint?')) return;
  const res = await fetch(`/api/complaint/${id}`, { method: 'DELETE' });
  if ((await res.json()).success) {
    const row = document.getElementById(`row-${id}`);
    if (row) row.style.animation = 'fadeOut .3s forwards';
    setTimeout(() => { if(row) row.remove(); }, 300);
  }
}
