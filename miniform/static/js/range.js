document.addEventListener('DOMContentLoaded', () => {
  // Обрабатываем все range-поля

  document.querySelectorAll('input[type="range"]').forEach(rangeInput => {
    // Устанавливаем значения по умолчанию
    const min = parseInt(rangeInput.min) || 0;
    const max = parseInt(rangeInput.max) || 100;
    const defaultValue = Math.floor((min + max) / 2);

    rangeInput.min = min;
    rangeInput.max = max;
    rangeInput.value = rangeInput.value || defaultValue;

    // Создаем индикатор значения
    const bubble = document.createElement('div');
    bubble.className = 'range-bubble';
    bubble.textContent = rangeInput.value;
    rangeInput.parentNode.appendChild(bubble);

    // Функция обновления позиции
    const updateBubble = () => {
      const currentValue = parseInt(rangeInput.value);
      const percent = (currentValue - min) / (max - min);
      const rangeWidth = 249; // Фиксированная ширина range
      const bubbleWidth = bubble.offsetWidth;

      // Позиция индикатора относительно range
      bubble.style.left = `${percent * rangeWidth - bubbleWidth / 2}px`;
      bubble.textContent = currentValue;
    };

    // Инициализация и обработчики
    updateBubble();
    rangeInput.addEventListener('input', updateBubble);
    window.addEventListener('resize', updateBubble);
  });
});