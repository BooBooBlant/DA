import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, CheckButtons
from scipy import signal

# Зберігаємо згенерований шум, щоб він не змінювався, якщо не змінюються параметри шуму
current_noise = None
last_noise_mean = None
last_noise_covariance = None
last_t_length = 0 # Для відстеження зміни розміру масиву часу

def harmonic_with_noise(t, amplitude, frequency, phase, noise_mean, noise_covariance, show_noise=True):
    """
    Генерує гармоніку та накладає на неї шум.
    Якщо параметри шуму не змінюються, використовує попередньо згенерований шум.
    """
    global current_noise, last_noise_mean, last_noise_covariance, last_t_length

    # Генеруємо чистий гармонійний сигнал
    clean_signal = amplitude * np.sin(2 * np.pi * frequency * t + phase)

    # Генеруємо шум тільки якщо параметри шуму змінились або масив часу змінився
    # Або якщо це перший запуск
    if (noise_mean != last_noise_mean or 
        noise_covariance != last_noise_covariance or
        len(t) != last_t_length or
        current_noise is None):
        
        print("Regenerating noise...") # Відладочний друк
        noise = np.random.normal(noise_mean, np.sqrt(noise_covariance), len(t))
        current_noise = noise
        last_noise_mean = noise_mean
        last_noise_covariance = noise_covariance
        last_t_length = len(t)
    else:
        # Використовуємо попередній шум, переконавшись, що він відповідає розміру t
        if len(current_noise) == len(t):
             noise = current_noise
        else: # Випадок, коли розмір t змінився, але параметри шуму ні - має бути рідко при фіксованому t
             print("Adjusting noise size...") # Відладочний друк
             noise = np.random.normal(noise_mean, np.sqrt(noise_covariance), len(t))
             current_noise = noise
             last_t_length = len(t)

    # Комбінуємо сигнал з шумом, якщо show_noise є True
    return clean_signal + (noise if show_noise else 0), clean_signal

def update(val):
    """
    Оновлює графік при зміні параметрів.
    """
    # Отримуємо поточні значення параметрів
    amp = amp_slider.val
    freq = freq_slider.val
    phase = phase_slider.val
    noise_mean = noise_mean_slider.val
    noise_cov = noise_cov_slider.val
    
    # Генеруємо новий сигнал (з можливим перегенеруванням шуму всередині функції)
    # Якщо show_noise вимкнено, функція поверне чисту гармоніку без додавання шуму
    noisy_signal, clean_signal_for_filter = harmonic_with_noise(t, amp, freq, phase, 
                                                               noise_mean, noise_cov, 
                                                               show_noise.get_status()[0])
    
    # Застосовуємо фільтр Баттерворта
    # Важливо: фільтрувати потрібно завжди сигнал З ШУМОМ, навіть якщо шум не відображається.
    # Це відповідає реальному сценарію, де ми фільтруємо отриманий (шумний) сигнал.
    b, a = signal.butter(4, cutoff_slider.val, fs=100) # 4й порядок, частота зрізу, частота дискретизації
    filtered_signal = signal.filtfilt(b, a, noisy_signal if show_noise.get_status()[0] else clean_signal_for_filter + current_noise) 
    # Примітка: якщо шум приховано, ми все одно застосовуємо фільтр до чистого сигналу + збережений шум,
    # щоб показати результат фільтрації реального сигналу. Якщо show_noise вимкнено, 
    # noisy_signal в harmonic_with_noise буде просто clean_signal. 
    # Щоб фільтрувати завжди однаковий базовий шум, використовуємо збережений current_noise.
    # Уточнення: згідно з завданням "Якщо прапорець прибрано – відображати «чисту гармоніку», якщо ні – зашумлену."
    # Це стосується відображення *вихідного* сигналу (жовтого).
    # Фільтр має працювати з сигналом *до* приховування шуму.
    
    # Отже, генеруємо сигнал з шумом завжди, але відображаємо його опціонально.
    full_noisy_signal, _ = harmonic_with_noise(t, amp, freq, phase, noise_mean, noise_cov, show_noise=True) # Завжди з шумом для фільтрації
    b, a = signal.butter(4, cutoff_slider.val, fs=100)
    filtered_signal = signal.filtfilt(b, a, full_noisy_signal)

    # Оновлюємо дані на графіках
    line_noisy.set_ydata(noisy_signal) # Відображаємо зашумлений або чистий в залежності від чекбокса
    line_clean.set_ydata(filtered_signal) # Відображаємо відфільтрований сигнал
    ax.set_ylim(min(min(noisy_signal), min(filtered_signal)) - 0.2, 
                max(max(noisy_signal), max(filtered_signal)) + 0.2) # Динамічно змінюємо межі осі Y
    fig.canvas.draw_idle() # Оновлюємо полотно

def reset(event):
    """
    Скидає всі повзунки та чекбокси до початкових значень.
    """
    # Скидаємо всі повзунки
    amp_slider.reset()
    freq_slider.reset()
    phase_slider.reset()
    noise_mean_slider.reset()
    noise_cov_slider.reset()
    cutoff_slider.reset()
    
    # Скидаємо чекбокс (активуємо перший елемент, що відповідає True)
    show_noise.set_active(0) # Встановлюємо Show Noise як активний (True)

# Створюємо масив часу
t = np.linspace(0, 10, 1000) # 10 секунд, 1000 точок

# Початкові параметри
initial_amp = 1.0
initial_freq = 0.5
initial_phase = 0
initial_noise_mean = 0.0
initial_noise_cov = 0.1
initial_cutoff = 2.0 # Зменшимо початкову частоту зрізу для кращої демонстрації фільтрації

# Створюємо вікно та область для графіка
fig, ax = plt.subplots(figsize=(10, 8))
plt.subplots_adjust(left=0.1, bottom=0.4) # Збільшуємо нижній відступ для повзунків

# Генеруємо початковий сигнал
# При першому виклику шум буде згенеровано
noisy_signal, clean_signal_for_filter = harmonic_with_noise(t, initial_amp, initial_freq, initial_phase,
                                                            initial_noise_mean, initial_noise_cov, show_noise=True)

# Застосовуємо початкову фільтрацію
b, a = signal.butter(4, initial_cutoff, fs=100)
filtered_signal = signal.filtfilt(b, a, noisy_signal) # Фільтруємо початковий зашумлений сигнал

# Малюємо сигнали
# Жовта лінія - зашумлений сигнал (або чистий, якщо чекбокс вимкнено)
line_noisy, = plt.plot(t, noisy_signal, color='orange', alpha=0.8, label='Зашумлений сигнал')
# Синя лінія - відфільтрований сигнал
line_clean, = plt.plot(t, filtered_signal, color='blue', label='Відфільтрований сигнал')

# Налаштування графіка
ax.set_xlabel("Час [с]")
ax.set_ylabel("Амплітуда")
ax.set_title("Візуалізація гармоніки з шумом та фільтрацією")
ax.grid(True)
ax.legend()
ax.set_ylim(min(min(noisy_signal), min(filtered_signal)) - 0.2, 
            max(max(noisy_signal), max(filtered_signal)) + 0.2) # Встановлюємо початкові межі Y

# Створюємо області для повзунків
slider_color = 'lightgoldenrodyellow'
ax_amp = plt.axes([0.1, 0.35, 0.65, 0.03], facecolor=slider_color)
ax_freq = plt.axes([0.1, 0.30, 0.65, 0.03], facecolor=slider_color)
ax_phase = plt.axes([0.1, 0.25, 0.65, 0.03], facecolor=slider_color)
ax_noise_mean = plt.axes([0.1, 0.20, 0.65, 0.03], facecolor=slider_color)
ax_noise_cov = plt.axes([0.1, 0.15, 0.65, 0.03], facecolor=slider_color)
ax_cutoff = plt.axes([0.1, 0.10, 0.65, 0.03], facecolor=slider_color) # Повзунок для частоти зрізу фільтра

# Створюємо повзунки
amp_slider = Slider(ax_amp, 'Амплітуда', 0.1, 2.0, valinit=initial_amp)
freq_slider = Slider(ax_freq, 'Частота', 0.1, 2.0, valinit=initial_freq)
phase_slider = Slider(ax_phase, 'Фаза', -np.pi, np.pi, valinit=initial_phase)
noise_mean_slider = Slider(ax_noise_mean, 'Шум (сер.)', -0.5, 0.5, valinit=initial_noise_mean)
noise_cov_slider = Slider(ax_noise_cov, 'Шум (дисп.)', 0.001, 0.5, valinit=initial_noise_cov) # Мін дисп. > 0
cutoff_slider = Slider(ax_cutoff, 'Частота зрізу', 0.1, 10.0, valinit=initial_cutoff)

# Створюємо кнопку "Скинути"
reset_ax = plt.axes([0.8, 0.025, 0.1, 0.04])
reset_button = Button(reset_ax, 'Скинути', color=slider_color)

# Створюємо чекбокс "Показати шум"
noise_ax = plt.axes([0.8, 0.075, 0.15, 0.04])
show_noise = CheckButtons(noise_ax, ['Показати шум'], [True]) # Початково активовано

# Прив'язуємо функції оновлення до подій зміни повзунків та чекбокса
amp_slider.on_changed(update)
freq_slider.on_changed(update)
phase_slider.on_changed(update)
noise_mean_slider.on_changed(update)
noise_cov_slider.on_changed(update)
cutoff_slider.on_changed(update)
show_noise.on_clicked(update) # Оновлюємо при зміні стану чекбокса

# Прив'язуємо функцію скидання до події натискання кнопки
reset_button.on_clicked(reset)

# Показуємо вікно
plt.show()