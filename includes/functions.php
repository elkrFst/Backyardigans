<?php

function getProjectInfo(): array {
    return [
        'title' => 'Smart Locker - Lockers Inteligentes con Reconocimiento Facial',
        'subtitle' => 'Acceso seguro, rápido y sin llaves mediante detección de rostro.',
        'description' => 'Un sistema inteligente de lockers que abre el acceso usando reconocimiento facial. Ideal para espacios de escuela, trabajo o gimnasio donde se requiere un método seguro y cómodo para abrir lockers sin llaves ni contraseñas tradicionales.',
        'features' => [
            'Acceso biométrico por reconocimiento facial.',
            'Registro automático de nuevos usuarios a los lockers disponibles.',
            'Panel administrativo para liberar y gestionar lockers.',
            'Detección de rostros en cámara en tiempo real.',
            'Diseño pensado en seguridad, usabilidad y control de acceso.'
        ],
        'sections' => [
            [
                'title' => 'Cómo funciona',
                'text' => 'El usuario se registra frente a la cámara y su rostro queda guardado como perfil. Al acercarse nuevamente, el sistema compara el rostro con los perfiles registrados y abre automáticamente el locker asignado.'
            ],
            [
                'title' => 'Beneficios',
                'text' => 'El acceso sin llaves reduce riesgos de pérdida y duplicado de accesos. Facilita la administración centralizada de lockers y crea una experiencia moderna y ágil para los usuarios.'
            ],
            [
                'title' => 'Aplicaciones',
                'text' => 'Este proyecto es útil en universidades, gimnasios, oficinas y eventos donde se necesite un sistema de lockers inteligente con acceso biométrico.'
            ]
        ],
        'technology' => [
            [
                'name' => 'Reconocimiento Facial',
                'description' => 'Permite abrir el locker automáticamente con una verificación biométrica del rostro.'
            ],
            [
                'name' => 'Cámara en tiempo real',
                'description' => 'Captura continua de imágenes para detectar el rostro del usuario al instante.'
            ],
            [
                'name' => 'Base de datos MySQL',
                'description' => 'Almacena usuarios, roles y registros de acceso de forma segura.'
            ],
            [
                'name' => 'Interfaz gráfica intuitiva',
                'description' => 'Diseñada para usuarios y administradores, con flujos claros y control total del sistema.'
            ]
        ]
    ];
}

function getTeamMembers(): array {
    return [
        [
            'name' => 'Kristopher Alexander Guzman',
            'photo' => 'assets/photos/kristopher.jpg',
            'role' => 'Desarrollador principal',
            'bio' => 'Líder del proyecto, encargado del diseño del sistema y la arquitectura general.'
        ],
        [
            'name' => 'ALAN AMADOR ALCARAZ MALTA',
            'photo' => 'assets/photos/alan.jpg',
            'role' => 'Desarrollador',
            'bio' => 'Responsable de la integración del reconocimiento facial y optimizaciones.'
        ],
        [
            'name' => 'ANGEL RAFAEL FRIEDMAN MARIZ CORTES',
            'photo' => 'assets/photos/angel.jpg',
            'role' => 'Desarrollador',
            'bio' => 'Encargado del flujo de registro y la lógica de lockers.'
        ],
        [
            'name' => 'JUAN MIGUEL ANGEL RINCON HERNANDEZ',
            'photo' => 'assets/photos/juan.jpg',
            'role' => 'Desarrollador',
            'bio' => 'Responsable de la UI y la experiencia de usuario en la aplicación.'
        ],
        [
            'name' => 'MAXIMO ALESSANDRO VILLA RIVERA',
            'photo' => 'assets/photos/maximo.jpg',
            'role' => 'Desarrollador',
            'bio' => 'Encargado de la base de datos y el mantenimiento del proyecto.'
        ]
    ];
}

function renderHeader(string $title, string $subtitle): void {
    echo "<header class='site-header'>\n";
    echo "  <div class='wrapper'>\n";
    echo "    <h1>$title</h1>\n";
    echo "    <p>$subtitle</p>\n";
    echo "  </div>\n";
    echo "</header>\n";
}

function renderSection(string $title, string $content, string $class = ''): void {
    echo "<section class='content-section $class'>\n";
    echo "  <div class='wrapper'>\n";
    echo "    <h2>$title</h2>\n";
    echo $content;
    echo "  </div>\n";
    echo "</section>\n";
}

function renderFeatureList(array $features): void {
    echo "<ul class='feature-list'>\n";
    foreach ($features as $feature) {
        echo "  <li>$feature</li>\n";
    }
    echo "</ul>\n";
}

function renderFileList(array $files): void {
    echo "<div class='file-list'>\n";
    foreach ($files as $file) {
        $name = htmlspecialchars($file['name']);
        $description = htmlspecialchars($file['description']);
        echo "  <div class='file-item'><strong>$name</strong><p>$description</p></div>\n";
    }
    echo "</div>\n";
}

function renderTeam(array $members): void {
    echo "<div class='team-grid'>\n";
    foreach ($members as $member) {
        $name = htmlspecialchars($member['name']);
        $role = htmlspecialchars($member['role']);
        $bio = htmlspecialchars($member['bio']);
        $photo = htmlspecialchars($member['photo']);
        echo "  <article class='team-card'>\n";
        echo "    <div class='team-photo' style='background-image: url($photo);'></div>\n";
        echo "    <div class='team-info'>\n";
        echo "      <h3>$name</h3>\n";
        echo "      <p class='team-role'>$role</p>\n";
        echo "      <p>$bio</p>\n";
        echo "    </div>\n";
        echo "  </article>\n";
    }
    echo "</div>\n";
}

function renderFooter(): void {
    $year = date('Y');
    echo "<footer class='site-footer'>\n";
    echo "  <div class='wrapper'>\n";
    echo "    <p>Proyecto Smart Locker - Página creada en PHP | $year</p>\n";
    echo "  </div>\n";
    echo "</footer>\n";
}
