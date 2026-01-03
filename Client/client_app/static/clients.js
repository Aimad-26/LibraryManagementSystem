function openModal(mode) {
    const modal = document.getElementById('clientModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');
    
    modal.classList.add('show');
    
    if (mode === 'add') {
        title.textContent = 'Ajouter un Client';
        body.innerHTML = `
            <form method="post" action="/clients/add/">
                {% csrf_token %}
                <div class="form-group">
                    <label>Nom *</label>
                    <input type="text" name="nom" required>
                </div>
                <div class="form-group">
                    <label>Prénom *</label>
                    <input type="text" name="prenom" required>
                </div>
                <div class="form-group">
                    <label>Email *</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Téléphone *</label>
                    <input type="tel" name="telephone" required>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn-primary">Ajouter</button>
                    <button type="button" class="btn-secondary" onclick="closeModal()">Annuler</button>
                </div>
            </form>
        `;
    }
}

function editClient(id, nom, prenom, email, telephone) {
    const modal = document.getElementById('clientModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');
    
    modal.classList.add('show');
    title.textContent = 'Modifier le Client';
    
    body.innerHTML = `
        <form method="post" action="/clients/edit/${id}/">
            {% csrf_token %}
            <div class="form-group">
                <label>Nom *</label>
                <input type="text" name="nom" value="${nom}" required>
            </div>
            <div class="form-group">
                <label>Prénom *</label>
                <input type="text" name="prenom" value="${prenom}" required>
            </div>
            <div class="form-group">
                <label>Email *</label>
                <input type="email" name="email" value="${email}" required>
            </div>
            <div class="form-group">
                <label>Téléphone *</label>
                <input type="tel" name="telephone" value="${telephone}" required>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn-primary">Enregistrer</button>
                <button type="button" class="btn-secondary" onclick="closeModal()">Annuler</button>
            </div>
        </form>
    `;
}

function viewClient(id, nom, prenom, email, telephone, dateInscription, emprunts) {
    const modal = document.getElementById('clientModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');
    
    modal.classList.add('show');
    title.textContent = 'Détails du Client';
    
    body.innerHTML = `
        <div class="info-row">
            <div class="info-icon">👤</div>
            <div class="info-content">
                <div class="info-label">Nom Complet</div>
                <div class="info-value">${nom} ${prenom}</div>
            </div>
        </div>
        <div class="info-row">
            <div class="info-icon">📧</div>
            <div class="info-content">
                <div class="info-label">Email</div>
                <div class="info-value">${email}</div>
            </div>
        </div>
        <div class="info-row">
            <div class="info-icon">📱</div>
            <div class="info-content">
                <div class="info-label">Téléphone</div>
                <div class="info-value">${telephone}</div>
            </div>
        </div>
        <div class="info-row">
            <div class="info-icon">📅</div>
            <div class="info-content">
                <div class="info-label">Date d'inscription</div>
                <div class="info-value">${dateInscription}</div>
            </div>
        </div>
        <div class="info-row">
            <div class="info-icon">📚</div>
            <div class="info-content">
                <div class="info-label">Emprunts actifs</div>
                <div class="info-value">${emprunts} livre(s)</div>
            </div>
        </div>
        <div class="form-actions">
            <button type="button" class="btn-secondary" onclick="closeModal()">Fermer</button>
        </div>
    `;
}

function deleteClient(id, name) {
    if (confirm(`Êtes-vous sûr de vouloir supprimer le client "${name}" ?`)) {
        window.location.href = `/clients/delete/${id}/`;
    }
}

function closeModal() {
    document.getElementById('clientModal').classList.remove('show');
}