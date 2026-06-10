<?php
require_once __DIR__ . '/includes/functions.php';

$project = getProjectInfo();
$team = getTeamMembers();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo htmlspecialchars($project['title']); ?></title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <?php renderHeader($project['title'], $project['subtitle']); ?>

    <main class="wrapper page-shell">
        <div class="tabs">
            <button class="tab-button active" data-tab="proyecto">Acerca del proyecto</button>
            <button class="tab-button" data-tab="tecnologia">Tecnología usada</button>
            <button class="tab-button" data-tab="equipo">Sobre nosotros</button>
        </div>

        <section id="proyecto" class="tab-content active">
            <div class="hero-card">
                <div>
                    <span class="eyebrow">Lockers inteligentes</span>
                    <h2>Acceso sin llaves basado en reconocimiento facial</h2>
                    <p>Tu cuerpo es la llave. Nuestro sistema identifica el rostro, verifica el usuario y abre el locker asignado de forma segura y rápida.</p>
                </div>
                <div class="hero-actions">
                    <a href="#caracteristicas" class="button">Ver características</a>
                </div>
            </div>

            <div class="feature-grid" id="caracteristicas">
                <?php foreach ($project['features'] as $feature): ?>
                    <article class="feature-card">
                        <div class="feature-icon"></div>
                        <h3>🔹 <?php echo htmlspecialchars($feature); ?></h3>
                        <p>Una solución moderna para mejorar la seguridad y la experiencia de acceso a lockers.</p>
                        <div class="feature-overlay">Haz hover y descubre más</div>
                    </article>
                <?php endforeach; ?>
            </div>

            <!-- Sección visual de lockers con emojis -->
            <div style="margin-top:28px;">
                <h3 style="margin:0 0 8px 0;">🔒 Estado de Lockers</h3>
                <p style="margin:0 0 12px 0;color:rgba(248,250,252,0.8);">Visión rápida del estado actual de los lockers. Usa el panel administrativo para cambios reales.</p>

                <?php
                // Datos demo — en producción se debería consultar la base de datos
                $lockers = [
                    ['locker' => 1, 'estado' => 'Ocupado', 'usuario' => 'Admin'],
                    ['locker' => 2, 'estado' => 'Libre', 'usuario' => ''],
                    ['locker' => 3, 'estado' => 'Libre', 'usuario' => ''],
                    ['locker' => 4, 'estado' => 'Libre', 'usuario' => '']
                ];
                ?>

                <div class="locker-grid">
                    <?php foreach ($lockers as $l):
                        $isFree = strtolower($l['estado']) === 'libre';
                        $emoji = $isFree ? '🟢' : '🔒';
                    ?>
                    <article class="locker-card">
                        <div class="locker-emoji"><?php echo $emoji; ?></div>
                        <div>
                            <h4>Locker <?php echo $l['locker']; ?></h4>
                            <p class="locker-user"><?php echo $l['usuario'] ? htmlspecialchars($l['usuario']) : 'Disponible'; ?></p>
                        </div>
                        <div class="locker-status <?php echo $isFree ? 'free' : 'occupied'; ?>"><?php echo $l['estado']; ?></div>
                    </article>
                    <?php endforeach; ?>
                </div>
            </div>

            <div class="info-grid">
                <?php foreach ($project['sections'] as $section): ?>
                    <article class="info-card">
                        <h3><?php echo htmlspecialchars($section['title']); ?></h3>
                        <p><?php echo htmlspecialchars($section['text']); ?></p>
                    </article>
                <?php endforeach; ?>
            </div>
        </section>

        <section id="tecnologia" class="tab-content">
            <div class="hero-card" style="grid-template-columns: 1fr; gap: 24px;">
                <div>
                    <span class="eyebrow">Tecnología</span>
                    <h2>La pila técnica detrás de Smart Locker</h2>
                    <p>Combinamos visión por computadora, control inteligente de acceso y una interfaz moderna para entregar un sistema confiable y escalable.</p>
                </div>
            </div>
            <div class="feature-grid">
                <?php foreach ($project['technology'] as $tech): ?>
                    <article class="feature-card">
                        <div class="feature-icon"></div>
                        <h3><?php echo htmlspecialchars($tech['name']); ?></h3>
                        <p><?php echo htmlspecialchars($tech['description']); ?></p>
                        <div class="feature-overlay">Explora cómo mejora el sistema</div>
                    </article>
                <?php endforeach; ?>
            </div>
        </section>

        <section id="equipo" class="tab-content">
            <div class="team-intro">
                <h2>Equipo de desarrollo</h2>
                <p>Somos el equipo detrás de Smart Locker. Diseñamos esta solución para combinar biometría, automatización y administración inteligente de lockers.</p>
            </div>
            <?php renderTeam($team); ?>
        </section>
    </main>

    <?php renderFooter(); ?>
    <script src="assets/js/app.js"></script>
</body>
</html>
