import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. DATI SPERIMENTALI
# ==========================================

payloads = [8, 24, 48, 96, 192]
labels_payload = [f"{p} B" for p in payloads]

# --- FREQUENZA 868 MHz ---
lat_868_2400 = [2.9062, 2.9060, 2.9546, 2.9561, 3.0543]
thr_868_2400 = [x * 8 for x in [2.75, 8.26, 16.25, 32.48, 62.86]]
loss_868_2400 = [50.0, 33.33, 25.0, 33.33, 28.57]
# PPS Calcolato (1 / Latenza)
pps_868_2400 = [1/x for x in lat_868_2400]

lat_868_9600 = [2.5554, 2.5549, 2.5551, 2.6053, 2.6052]
thr_868_9600 = [x * 8 for x in [3.13, 9.39, 18.79, 36.85, 73.70]]
loss_868_9600 = [0.0, 0.0, 0.0, 0.0, 16.67]
pps_868_9600 = [1/x for x in lat_868_9600]


# --- FREQUENZA 433 MHz ---
lat_433_2400 = [2.9061, 2.9059, np.nan, 2.9560, np.nan]
thr_433_2400 = [x * 8 for x in [2.75, 8.26, 0.0, 32.48, 0.0]]
loss_433_2400 = [50.0, 50.0, 71.43, 66.67, 75.0]
# PPS Calcolato (Gestione NaN)
pps_433_2400 = [1/x if not np.isnan(x) else 0 for x in lat_433_2400]

lat_433_9600 = [2.5552, 2.5550, 2.5559, 2.6051, 2.6038]
thr_433_9600 = [x * 8 for x in [3.13, 9.39, 18.78, 36.85, 73.74]]
loss_433_9600 = [0.0, 33.33, 25.0, 33.33, 28.57]
pps_433_9600 = [1/x for x in lat_433_9600]


# ==========================================
# 2. FUNZIONE DI SUPPORTO PER ETICHETTE
# ==========================================
def add_labels(ax, x, y, color, offset=10, is_bar=False, fmt="{:.2f}"):
    for i, val in enumerate(y):
        if np.isnan(val) or val == 0: continue 
        
        txt = f"{val:.0f}%" if is_bar else fmt.format(val)
        
        if is_bar:
             ax.annotate(txt, (i + offset, val), ha='center', va='bottom', fontsize=8, color='black')
        else:
            ax.annotate(txt, (x[i], val), xytext=(0, offset), textcoords='offset points', 
                        ha='center', va='center', color=color, fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", alpha=0.7, edgecolor='none'))

# ==========================================
# 3. GENERAZIONE GRAFICI (Griglia 2x2)
# ==========================================
def create_figure(freq_name, lat1, lat2, thr1, thr2, loss1, loss2, pps1, pps2):
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Creiamo una griglia 2x2
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Analisi Completa LoRa: {freq_name}', fontsize=16, weight='bold')

    # --- 1. LATENZA (Alto Sinistra) ---
    ax = axs[0, 0]
    ax.plot(payloads, lat1, 'o-', color='#0052cc', label='2400 bps')
    ax.plot(payloads, lat2, 's--', color='#d62728', label='9600 bps')
    add_labels(ax, payloads, lat1, '#0052cc', 15)
    add_labels(ax, payloads, lat2, '#d62728', -15)
    ax.set_title('Latenza (RTT)')
    ax.set_ylabel('Secondi')
    ax.set_xticks(payloads)
    ax.legend()
    ax.grid(True, linestyle=':')

    # --- 2. THROUGHPUT (Alto Destra) ---
    ax = axs[0, 1]
    ax.plot(payloads, thr1, 'o-', color='#2ca02c', label='2400 bps')
    ax.plot(payloads, thr2, 's--', color='#ff7f0e', label='9600 bps')
    add_labels(ax, payloads, thr1, '#2ca02c', -15, fmt="{:.0f}")
    add_labels(ax, payloads, thr2, '#ff7f0e', 15, fmt="{:.0f}")
    ax.set_title('Throughput (Goodput)')
    ax.set_ylabel('bit/s (bps)')
    ax.set_xticks(payloads)
    ax.legend()
    ax.grid(True, linestyle=':')

    # --- 3. PPS (Packets Per Second) (Basso Sinistra) ---
    ax = axs[1, 0]
    ax.plot(payloads, pps1, 'D-', color='purple', label='2400 bps')
    ax.plot(payloads, pps2, '^--', color='brown', label='9600 bps')
    add_labels(ax, payloads, pps1, 'purple', 15)
    add_labels(ax, payloads, pps2, 'brown', -15)
    ax.set_title('Capacità di Invio (PPS)')
    ax.set_ylabel('Pacchetti / Secondo')
    ax.set_xlabel('Payload (Byte)')
    ax.set_xticks(payloads)
    ax.legend()
    ax.grid(True, linestyle=':')

    # --- 4. PACKET LOSS (Basso Destra) ---
    ax = axs[1, 1]
    x = np.arange(len(labels_payload))
    width = 0.35
    ax.bar(x - width/2, loss1, width, label='2400 bps', color='#0052cc', alpha=0.7)
    ax.bar(x + width/2, loss2, width, label='9600 bps', color='#d62728', alpha=0.7)
    
    # Etichette barre
    for i, v in enumerate(loss1):
        if v > 0: ax.text(i - width/2, v + 1, f"{v:.0f}%", ha='center', fontsize=8)
    for i, v in enumerate(loss2):
        if v > 0: ax.text(i + width/2, v + 1, f"{v:.0f}%", ha='center', fontsize=8)

    ax.set_title('Packet Loss Rate')
    ax.set_ylabel('Perdita (%)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_payload)
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(True, axis='y', linestyle=':')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95], h_pad=3.0)
    filename = f'grafici_completi_{freq_name.replace(" ", "")}.png'
    plt.savefig(filename, dpi=300)
    print(f"✅ Salvato: {filename}")

# ==========================================
# 4. ESECUZIONE
# ==========================================

create_figure("868 MHz", lat_868_2400, lat_868_9600, thr_868_2400, thr_868_9600, loss_868_2400, loss_868_9600, pps_868_2400, pps_868_9600)
create_figure("433 MHz", lat_433_2400, lat_433_9600, thr_433_2400, thr_433_9600, loss_433_2400, loss_433_9600, pps_433_2400, pps_433_9600)

plt.show()