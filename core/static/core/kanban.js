let draggedTask = null;

const cards = document.querySelectorAll('.task-card');
const columns = document.querySelectorAll('.task-list');

cards.forEach(card => {

    card.addEventListener('dragstart', function () {
        draggedTask = this;
        this.classList.add('dragging');
    });

    card.addEventListener('dragend', function () {
        this.classList.remove('dragging');
        draggedTask = null;
    });

});

columns.forEach(column => {

    column.addEventListener('dragover', function (event) {
        event.preventDefault();
        this.classList.add('drag-over');
    });

    column.addEventListener('dragleave', function () {
        this.classList.remove('drag-over');
    });

    column.addEventListener('drop', async function (event) {

        event.preventDefault();

        this.classList.remove('drag-over');

        if (!draggedTask) return;

        const taskForm = draggedTask.querySelector('.status-form');
        const statusSelect = taskForm.querySelector('select');

        const newStatus = this.dataset.status;

        if (statusSelect.value === newStatus) return;

        const oldStatus = statusSelect.value;

        statusSelect.value = newStatus;

        const formData = new FormData(taskForm);

        try {

            const response = await fetch(taskForm.action, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Unable to update task');
            }

            location.reload();

        } catch (error) {

            statusSelect.value = oldStatus;

            alert('Task update failed. Please try again.');

        }

    });

});