import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
import time
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# ==========================================
# 1. FAKE WEB SERVER (UNTUK RENDER & UPTIMEROBOT)
# ==========================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bypass Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Fake web server running on port {port}")
    server.serve_forever()

web_thread = threading.Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()

# ==========================================
# 2. KONFIGURASI BOT DISCORD
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot Bypass {bot.user} sudah aktif dan online!")
    try:
        synced = await bot.tree.sync()
        print(f"Berhasil mensinkronkan {len(synced)} slash commands.")
    except Exception as e:
        print(f"Gagal sinkronisasi command: {e}")

# ==========================================
# 3. VIEW / TOMBOL INTERAKTIF (BUTTONS)
# ==========================================
class BypassView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Tombol navigasi / link tambahan di bawah embed
        self.add_item(discord.ui.Button(label="VSPhone", url="https://example.com", emoji="🎮"))
        self.add_item(discord.ui.Button(label="Discord", url="https://discord.gg/yourlink", emoji="🌐"))
        self.add_item(discord.ui.Button(label="Website", url="https://example.com", emoji="💻"))
        self.add_item(discord.ui.Button(label="API", url="https://bypass.vip", emoji="⚡"))

# ==========================================
# 4. SLASH COMMAND /BYPASS
# ==========================================
@bot.tree.command(name="bypass", description="Mengambil key secara otomatis")
@app_commands.describe(link="Masukkan link tujuan")
async def bypass(interaction: discord.Interaction, link: str):
    # Menggunakan ephemeral=False supaya hasilnya muncul secara publik di channel
    await interaction.response.defer(ephemeral=False)

    start_time = time.time()
    
    # Ganti dengan endpoint API bypass yang aktif
    api_url = f"https://api.bypass.vip/bypass?url={link}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Mengambil hasil dari berbagai kemungkinan key JSON response
                    bypassed_url = data.get("result") or data.get("destination") or data.get("key")
                    
                    elapsed_time = round(time.time() - start_time, 1)

                    # Validasi jika yang muncul pesan error shutdown
                    if bypassed_url and "SHUT DOWN" in str(bypassed_url):
                        bypassed_url = None

                    if bypassed_url:
                        avatar_url = interaction.user.display_avatar.url
                        username = interaction.user.name

                        # Membuat Embed bersih yang hanya menampilkan Result
                        embed = discord.Embed(
                            title="Bypass Successful",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Result", value=f"`{bypassed_url}`", inline=False)
                        embed.set_footer(
                            text=f"Requested by {username} • Processed in {elapsed_time}s",
                            icon_url=avatar_url
                        )

                        view = BypassView()
                        await interaction.followup.send(embed=embed, view=view)
                    else:
                        await interaction.followup.send(
                            "❌ API sedang gangguan atau link tidak valid/tidak didukung.",
                            ephemeral=True
                        )
                else:
                    await interaction.followup.send(
                        "⚠️ Server API bypass sedang mengalami gangguan.",
                        ephemeral=True
                    )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏱️ Koneksi ke server bypass *timeout*. Silakan coba lagi.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Terjadi kesalahan: `{e}`",
                ephemeral=True
            )

# ==========================================
# 5. MENJALANKAN BOT
# ==========================================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("⚠️ ERROR: Token bot Discord tidak ditemukan!")
else:
    bot.run(TOKEN)
