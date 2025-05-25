
import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Slider, Button, Select, Toggle
from bokeh.layouts import column, row
from bokeh.io import curdoc

# Зберігаємо згенерований шум, щоб він не змінювався, якщо не змінюються параметри шуму
current_noise = None
last_noise_mean = None
last_noise_covariance = None
last_t_length = 0 # Для відстеження зміни розміру масиву часу

def harmonic_with_noise(t, amplitude, frequency, phase, noise_mean, noise_covariance):
    """
    Генерує гармоніку та накладає на неї шум.
    Якщо параметри шуму не змінюються, використовує попередньо згенерований шум.
    Завжди повертає чистий сигнал та сигнал з шумом.
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

        #print("Regenerating noise...") # Debug print
        # Переконуємось, що коваріація не від'ємна для np.random.normal (використовуємо std dev)
        noise = np.random.normal(noise_mean, np.sqrt(max(0, noise_covariance)), len(t))
        current_noise = noise
        last_noise_mean = noise_mean
        last_noise_covariance = noise_covariance
        last_t_length = len(t)
    else:
        # Використовуємо попередній шум, переконавшись, що він відповідає розміру t
        if len(current_noise) == len(t):
             noise = current_noise
        else: # Випадок, коли розмір t змінився, але параметри шуму ні - має бути рідко при фіксованому t
             #print("Adjusting noise size...") # Debug print
             noise = np.random.normal(noise_mean, np.sqrt(max(0, noise_covariance)), len(t))
             current_noise = noise
             last_t_length = len(t)

    # Комбінуємо сигнал з шумом
    noisy_signal = clean_signal + noise

    return clean_signal, noisy_signal

def custom_moving_average_filter(signal, window_size):
    """
    Apply a moving average filter using numpy convolution.
    Handles edge cases by using mode='same'.
    """
    if window_size <= 1:
        return signal
    # Ensure window_size is an integer
    window_size = int(window_size)
    # Create a rectangular window kernel
    kernel = np.ones(window_size) / window_size
    # Apply convolution
    filtered_signal = np.convolve(signal, kernel, mode='same')
    return filtered_signal

# Створюємо масив часу
t = np.linspace(0, 10, 1000)

# Початкові параметри
initial_amp = 1.0
initial_freq = 0.5
initial_phase = 0
initial_noise_mean = 0.0
initial_noise_cov = 0.1
initial_window_size = 10

# Генеруємо початкові дані
initial_clean_signal, initial_noisy_signal = harmonic_with_noise(t, initial_amp, initial_freq, initial_phase,
                                                                   initial_noise_mean, initial_noise_cov)
initial_filtered_signal = custom_moving_average_filter(initial_noisy_signal, initial_window_size)

# Створюємо джерело даних Bokeh
source = ColumnDataSource(data=dict(t=t,
                                   clean_signal=initial_clean_signal,
                                   noisy_signal=initial_noisy_signal,
                                   filtered_signal=initial_filtered_signal))

# Створюємо перший графік (Вихідний сигнал)
plot1 = figure(height=300, width=800, title="Вихідний сигнал (Чистий / Зашумлений)",
               tools="pan,wheel_zoom,box_zoom,reset,save")
line_clean = plot1.line('t', 'clean_signal', source=source, line_width=2, color='blue', legend_label="Чистий сигнал")
line_noisy = plot1.line('t', 'noisy_signal', source=source, line_width=2, color='orange', legend_label="Зашумлений сигнал", visible=True) # Початково показуємо зашумлений

# Створюємо другий графік (Відфільтрований сигнал)
plot2 = figure(height=300, width=800, title="Відфільтрований сигнал (Ковзне середнє)",
               tools="pan,wheel_zoom,box_zoom,reset,save", x_range=plot1.x_range) # Ділимо вісь X
line_filtered = plot2.line('t', 'filtered_signal', source=source, line_width=2, color='green', legend_label="Відфільтрований сигнал")

# Налаштування легенди
plot1.legend.location = "top_right"
plot1.legend.click_policy="hide" # Дозволяє приховувати/показувати лінії по кліку на легенді
plot2.legend.location = "top_right"
plot2.legend.click_policy="hide"

# Створюємо повзунки
amp_slider = Slider(start=0.1, end=2.0, value=initial_amp, step=.1, title="Амплітуда")
freq_slider = Slider(start=0.1, end=2.0, value=initial_freq, step=.1, title="Частота")
phase_slider = Slider(start=-np.pi, end=np.pi, value=initial_phase, step=np.pi/10, title="Фаза")
noise_mean_slider = Slider(start=-0.5, end=0.5, value=initial_noise_mean, step=.05, title="Шум (сер.)")
noise_cov_slider = Slider(start=0.001, end=0.5, value=initial_noise_cov, step=.01, title="Шум (дисп.)")
window_slider = Slider(start=1, end=50, value=initial_window_size, step=1, title="Розмір вікна фільтра")

# Створюємо спадне меню для вибору відображення на першому графіку
view_select = Select(title="Показати на верхньому графіку:", value="Зашумлений",
                     options=["Чистий", "Зашумлений"])

# Створюємо кнопку Reset
reset_button = Button(label="Скинути параметри")

# Функція оновлення даних
def update_data(attrname, old, new):
    """
    Оновлює джерело даних при зміні параметрів.
    """
    amp = amp_slider.value
    freq = freq_slider.value
    phase = phase_slider.value
    noise_mean = noise_mean_slider.value
    noise_cov = noise_cov_slider.value
    window_size = window_slider.value
    view_option = view_select.value

    # Генеруємо сигнали (завжди отримуємо чистий та зашумлений для подальшої обробки)
    clean_signal, noisy_signal = harmonic_with_noise(t, amp, freq, phase, noise_mean, noise_cov)

    # Застосовуємо власний фільтр до зашумленого сигналу
    filtered_signal = custom_moving_average_filter(noisy_signal, window_size)

    # Оновлюємо джерело даних
    source.data = dict(t=t,
                        clean_signal=clean_signal,
                        noisy_signal=noisy_signal,
                        filtered_signal=filtered_signal)

    # Керуємо видимістю ліній на першому графіку відповідно до вибору у спадному меню
    line_clean.visible = (view_option == "Чистий")
    line_noisy.visible = (view_option == "Зашумлений")


# Функція скидання параметрів
def reset_params():
    """
    Скидає повзунки та вибори до початкових значень і оновлює графік.
    """
    amp_slider.value = initial_amp
    freq_slider.value = initial_freq
    phase_slider.value = initial_phase
    noise_mean_slider.value = initial_noise_mean
    noise_cov_slider.value = initial_noise_cov
    window_slider.value = initial_window_size
    view_select.value = "Зашумлений" # Скидаємо вибір відображення

    # Оновлення графіка відбудеться автоматично через прив'язані нижче колбеки

# Прив'язуємо функцію оновлення до зміни значень повзунків та спадного меню
sliders = [amp_slider, freq_slider, phase_slider, noise_mean_slider, noise_cov_slider, window_slider]
for slider in sliders:
    slider.on_change('value', update_data)

view_select.on_change('value', update_data)

# Прив'язуємо функцію скидання до кнопки
reset_button.on_click(reset_params)

# Встановлюємо початкову видимість ліній відповідно до початкового значення view_select
line_clean.visible = (view_select.value == "Чистий")
line_noisy.visible = (view_select.value == "Зашумлений")

# Створюємо макет інтерфейсу
# Розміщуємо повзунки та кнопку збоку від графіків
controls = column(amp_slider, freq_slider, phase_slider,
                   noise_mean_slider, noise_cov_slider,
                   window_slider, view_select, reset_button)

# Розміщуємо графіки один під одним, а панель управління - поруч
layout = row(column(plot1, plot2), controls)

# Додаємо макет до кореневого елемента документа Bokeh
curdoc().add_root(layout)



