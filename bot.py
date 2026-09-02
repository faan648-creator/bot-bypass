import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import asyncio
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
# 3. SLASH COMMAND /BYPASS (KIRIM KE WEBHOOK)
# ==========================================
@bot.tree.command(name="bypass", description="Mengambil key Lynx secara otomatis dan mengirim hasilnya ke webhook")
@app_commands.describe(link="Masukkan link Lynx / Linkvertise tujuan")
async def bypass(interaction: discord.Interaction, link: str):
    await interaction.response.defer(ephemeral=True)

    api_url = f"https://api.bypass.vip/bypass?url={link}"
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        await interaction.followup.send(
            "⚠️ Variabel `DISCORD_WEBHOOK_URL` belum diset di Environment Variables Render!",
            ephemeral=True
        )
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    bypassed_url = data.get("result") or data.get("destination") or data.get("key")
                    
                    if bypassed_url:
                        # Kirim hasil bypass langsung ke Discord Webhook
                        webhook_payload = {
                            "content": (
                                f"🔗 **User:** {interaction.user.mention} (`{interaction.user.name}`)\n"
                                f"📥 **Input Link:** {link}\n"
                                f"🔑 **Bypassed Key / URL:**\n`{bypassed_url}`"
                            )
                        }
                        
                        async with session.post(webhook_url, json=webhook_payload) as wh_resp:
                            if wh_resp.status in [200, 204]:
                                await interaction.followup.send(
                                    "✅ **Berhasil!** Hasil bypass telah dikirim otomatis ke Discord Webhook.",
                                    ephemeral=True
                                )
                            else:
                                await interaction.followup.send(
                                    f"⚠️ Gagal mengirim ke webhook (Status: {wh_resp.status}).",
                                    ephemeral=True
                                )
                    else:
                        await interaction.followup.send(
                            "❌ Gagal mengekstrak key dari link tersebut. Pastikan link-nya valid!",
                            ephemeral=True
                        )
                else:
                    await interaction.followup.send(
                        "⚠️ Server API bypass sedang mengalami gangguan. Coba beberapa saat lagi.",
                        ephemeral=True
                    )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏱️ Koneksi ke server bypass *timeout*. Silakan coba lagi.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Terjadi kesalahan saat memproses bypass: `{e}`",
                ephemeral=True
            )

# ==========================================
# 4. MENJALANKAN BOT
# ==========================================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("⚠️ ERROR: Token bot Discord tidak ditemukan!")
else:
    bot.run(TOKEN)
