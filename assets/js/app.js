document.addEventListener('DOMContentLoaded', function () {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const target = button.dataset.tab;

            tabButtons.forEach(btn => btn.classList.toggle('active', btn === button));
            tabContents.forEach(content => {
                content.classList.toggle('active', content.id === target);
            });
        });
    });
});
