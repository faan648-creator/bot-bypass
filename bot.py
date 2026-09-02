import os
import time
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import discord
from discord import app_commands
from discord.ext import commands
from playwright.async_api import async_playwright

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
# 3. FUNGSI PLAYWRIGHT (AUTOMATION BYPASS)
# ==========================================
async def bypass_platorelay(target_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Membuka link tujuan dengan batas waktu 40 detik
            await page.goto(target_url, timeout=40000)
            
            # Waktu tunggu untuk verifikasi halaman/token awal
            await page.wait_for_timeout(8000)

            # Cek otomatis tombol "Continue" jika ada
            try:
                continue_btn = page.locator("text=Continue")
                if await continue_btn.count() > 0:
                    await continue_btn.first.click()
                    await page.wait_for_timeout(5000)
            except Exception:
                pass

            # Mengambil URL akhir hasil proses bypass
            final_url = page.url
            await browser.close()
            return final_url

        except Exception as e:
            await browser.close()
            print(f"Error automation: {e}")
            return None

# ==========================================
# 4. VIEW / TOMBOL INTERAKTIF (BUTTONS)
# ==========================================
class BypassView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="VSPhone", url="https://example.com", emoji="🎮"))
        self.add_item(discord.ui.Button(label="Discord", url="https://discord.gg/yourlink", emoji="🌐"))
        self.add_item(discord.ui.Button(label="Website", url="https://example.com", emoji="💻"))
        self.add_item(discord.ui.Button(label="Bypass Bot", url="https://example.com", emoji="⚡"))

# ==========================================
# 5. SLASH COMMAND /BYPASS
# ==========================================
@bot.tree.command(name="bypass", description="Mengambil key secara otomatis via Automation")
@app_commands.describe(link="Masukkan link platorelay tujuan")
async def bypass(interaction: discord.Interaction, link: str):
    # Wajib defer agar bot tidak mengalami error "The application did not respond"
    await interaction.response.defer(ephemeral=False)

    start_time = time.time()
    
    # Menjalankan mesin automation Playwright
    result_key = await bypass_platorelay(link)
    
    elapsed_time = round(time.time() - start_time, 1)

    if result_key:
        avatar_url = interaction.user.display_avatar.url
        username = interaction.user.name

        embed = discord.Embed(
            title="Bypass Successful",
            color=discord.Color.green()
        )
        embed.add_field(name="Result", value=f"`{result_key}`", inline=False)
        embed.set_footer(
            text=f"Requested by {username} • Processed in {elapsed_time}s",
            icon_url=avatar_url
        )

        view = BypassView()
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.followup.send(
            "❌ Gagal mendapatkan key atau proses automation timeout.",
            ephemeral=True
        )

# ==========================================
# 6. MENJALANKAN BOT
# ==========================================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("⚠️ ERROR: Token bot Discord tidak ditemukan!")
else:
    bot.run(TOKEN)
