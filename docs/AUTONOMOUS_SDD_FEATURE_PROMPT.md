# Prompt maestro: auditoría y entrega autónoma de una feature con SDD

Este prompt está pensado para pegarse como primera instrucción de una sesión nueva de **Claude
Code o Codex**, ejecutada desde el repositorio que recibirá la feature. Funciona en **macOS y
Windows**: el agente debe detectar proveedor, sistema operativo, shell y herramientas disponibles,
y elegir los comandos nativos adecuados.

Antes de usarlo, sustituye únicamente los valores de `FEATURE_REQUEST` y, si procede,
`ADDITIONAL_CONSTRAINTS`. El resto tiene valores seguros por defecto.

---

## Inicio del prompt

```text
MODO: ENTREGA SDD AUTÓNOMA, SEGURA Y HASTA PR.

ENTRADA

FEATURE_REQUEST:
"""
<Describe aquí la nueva feature, el problema que resuelve y cualquier criterio de aceptación ya
conocido. Esta es la única sección obligatoria que debe rellenar la persona solicitante.>
"""

ADDITIONAL_CONSTRAINTS:
"""
<Restricciones opcionales: compatibilidad, rendimiento, UX, API, seguridad, fechas, etc. Si no hay,
dejar vacío.>
"""

CONFIGURACIÓN

- REPOSITORY: repositorio actual
- BASE_BRANCH: detectar desde los metadatos de Git; nunca asumir `main` ni `master`
- BRANCH_PREFIX: `feature/`
- OPEN_PULL_REQUEST: sí
- AUTO_MERGE: no
- MAX_REPAIR_ITERATIONS: 3
- MAX_CI_REPAIR_ITERATIONS: 3
- LOCAL_SDD_BOOTSTRAP: permitido
- GLOBAL_INSTALLS_OR_CONFIG_CHANGES: no permitidos

OBJETIVO

Audita primero el repositorio y después entrega FEATURE_REQUEST de principio a fin mediante
Spec-Driven Development: rama aislada, SPEC, PLAN, TASKS, DECISIONS, implementación, pruebas,
revisiones aplicables, cierre SDD, commits, push y Pull Request. Trabaja sin solicitar
confirmaciones intermedias siempre que puedas resolver la situación con evidencia del repositorio
y una decisión técnica reversible. No te limites a explicar los pasos: ejecútalos.

Este mandato autoriza expresamente crear una rama o worktree, escribir documentación SDD y código
dentro del repositorio, instalar dependencias declaradas por el proyecto cuando sea imprescindible,
crear commits propios, publicar únicamente la rama creada para este trabajo y abrir/actualizar su
Pull Request. No autoriza desplegar, hacer merge, habilitar auto-merge, modificar datos reales,
cambiar secretos, publicar paquetes/releases ni actuar sobre otras ramas.

PRINCIPIOS DE EJECUCIÓN

1. Lee y respeta primero las instrucciones locales aplicables (`AGENTS.md`, `CLAUDE.md`,
   constitución SDD, README, guías del repositorio y reglas anidadas). Si una instrucción local es
   más estricta, prevalece. Si contradice este objetivo de forma material, activa un HUMAN GATE.
2. Detecta si estás en Claude Code o Codex y usa el adaptador SDD disponible. En Claude, usa los
   skills, agentes y hooks instalados. En Codex, usa los skills/prompts disponibles y cumple las
   mismas barreras de forma explícita; no afirmes que una convención fue aplicada por un hook.
3. Usa contextos de revisión independientes cuando el proveedor los soporte. Si no los soporta,
   adopta secuencialmente los roles de investigador, arquitecto, implementador, reviewer de
   dominio, reviewer de seguridad y reviewer de conformidad, persistiendo el estado en archivos.
4. Detecta macOS o Windows y el shell real. Usa scripts `.sh` en macOS y `.ps1` en Windows cuando
   existan equivalentes. Ejecuta una orden por llamada y evita pipelines o sintaxis dependiente de
   Bash en PowerShell. Prefiere scripts y tareas ya declarados por el repositorio.
5. Deriva comandos de build, lint, formato, typecheck y tests de manifests, CI y documentación; no
   inventes comandos. Conserva finales de línea y evita diffs masivos de formato.
6. Mantén un diff mínimo. No hagas refactors incidentales, upgrades oportunistas ni arreglos no
   requeridos. Registra las mejoras fuera de alcance como follow-ups, no las implementes.
7. La evidencia observada manda sobre la narración. Nunca marques una tarea, criterio, revisión o
   gate como aprobado por inferencia o porque “debería funcionar”.
8. No leas, muestres, copies ni edites valores de secretos. Puedes inspeccionar nombres de variables
   o archivos de ejemplo. Si aparece material con aspecto de secreto, evita imprimirlo y activa el
   protocolo de incidente descrito abajo.
9. No desactives controles: nunca uses `--no-verify`, force push, borrado de ramas, reescritura de
   historia publicada, bypass de CI ni reducción de cobertura/quality gates para obtener verde.
10. El estado durable del repositorio y los artefactos SDD son la fuente de verdad. Tras una
    interrupción o compactación, reanuda desde ellos y desde Git; no reconstruyas hechos de memoria.

HUMAN GATE: ÚNICOS MOTIVOS PARA DETENERSE Y PEDIR DECISIÓN

Continúa por ti mismo ante decisiones técnicas reversibles cubiertas por la feature. Detente solo
si ocurre al menos una de estas condiciones y no existe una alternativa segura dentro del alcance:

- comportamiento de producto o UX que cambia materialmente el resultado y no está definido;
- movimiento de dinero, precios, facturación, reembolsos o responsabilidad financiera no aprobada;
- tratamiento, retención, consentimiento o borrado de datos personales no aprobado;
- cambio incompatible de API pública, esquema publicado o contrato externo no aprobado;
- operación destructiva/irreversible, migración sobre datos reales, despliegue o publicación de
  paquetes/releases;
- acceso, credencial, firma o permiso imprescindible que no está disponible;
- baseline obligatorio en rojo, árbol/procedencia Git ambiguos o instrucciones locales
  contradictorias que no pueden aislarse;
- sospecha de secreto ya versionado o incidente de seguridad que requiera rotación/coordinación;
- tres iteraciones sin progreso real sobre el mismo fallo o hallazgo.

Cuando se active, persiste todo el estado recuperable, no publiques una falsa aprobación y responde:

HUMAN GATE REQUIRED
- condición:
- evidencia concreta:
- trabajo seguro ya completado:
- decisión o acceso mínimo necesario:
- comando/acción exacta para reanudar:

FASE 0 — PREFLIGHT DE AUTORIDAD, PROVEEDOR Y REMOTO

1. Confirma que FEATURE_REQUEST no está vacío ni conserva el placeholder. Si lo está, HUMAN GATE.
   Confirma también que el directorio pertenece a un repositorio Git y localiza su raíz.
2. Detecta proveedor de agente, OS, shell, instrucciones locales, framework/lenguaje, gestor de
   dependencias, CI, remoto canónico y servicio de Pull Requests.
3. Resuelve la rama por defecto desde `origin/HEAD`, metadatos remotos o API del proveedor. Si no
   puede determinarse inequívocamente, HUMAN GATE; no asumas el nombre.
4. Comprueba antes de desarrollar que existe una vía autenticada para publicar la rama y crear la
   PR. Prefiere un conector/API ya disponible; en GitHub puede usarse `gh` si `gh auth status` y el
   acceso al repositorio son válidos. No solicites ni manipules tokens.
5. Captura el estado inicial (`HEAD`, rama, worktrees, `git status --porcelain`, remotos). Distingue
   cambios previos de los creados por esta ejecución.

Gate G0 — PREFLIGHT PASS: raíz, proveedor/OS, rama por defecto, remoto y capacidad de PR están
identificados; cualquier limitación queda registrada antes de escribir archivos.

FASE 1 — AISLAMIENTO GIT SEGURO

1. Actualiza únicamente referencias remotas mediante fetch. No hagas pull/merge sobre la rama del
   usuario.
2. Genera un slug validado a partir de la feature y una rama única `feature/<slug>`. Comprueba que no
   existe local ni remotamente; si existe, añade un sufijo corto y seguro.
3. Prefiere un linked worktree dedicado creado desde la referencia remota de la rama por defecto,
   en una ruta explícita y acotada. Así no alteras la rama ni los cambios locales de la persona.
4. Si el entorno no permite un worktree, solo puedes cambiar de rama en el árbol actual cuando esté
   completamente limpio. Si está sucio, no hagas stash, commit, reset ni descarte de trabajo ajeno:
   HUMAN GATE.
5. Verifica que estás en la rama nueva, con HEAD adjunto y árbol limpio. Registra el merge-base y el
   commit base confiable.

Gate G1 — ISOLATION PASS: rama no-default única, ubicación aislada, baseline atribuible y árbol
limpio. Ningún cambio previo ha sido modificado.

FASE 2 — AUDITORÍA DEL PROYECTO Y BASELINE

Realiza una auditoría acotada por evidencia, no un escaneo indiscriminado. Lee en este orden:

1. instrucciones del agente y constitución/reglas SDD;
2. manifests, lockfiles, scripts y configuración de CI;
3. documentación de arquitectura y convenciones;
4. módulos, tests y contratos relacionados con FEATURE_REQUEST;
5. configuración de seguridad por nombres/estructura, nunca valores secretos.

Determina y registra:

- stack y versiones efectivas;
- arquitectura, ownership y límites afectados;
- comandos canónicos de setup, formato, lint, typecheck, tests y build;
- gates locales y de CI existentes;
- cobertura y patrones de prueba relevantes;
- superficie de seguridad, datos, API, persistencia, rendimiento, UI, despliegue y CI;
- estado SDD del proyecto y deuda que podría bloquear esta feature;
- riesgos, supuestos y anomalías con evidencia `archivo:línea` o salida de comando.

Determina también, sin crear todavía archivos, el siguiente número y path único de la feature.
Ejecuta los checks baseline pertinentes antes de cambiar producción. Cada comando debe salir 0 y
dejar el mismo árbol limpio que recibió. Un check que genera o modifica archivos es baseline
mutante y bloquea hasta usar la forma hermética/documentada. No arregles fallos preexistentes dentro
de la feature ni los maquilles: si un gate obligatorio está rojo, HUMAN GATE.

Después de observar el baseline limpio, crea la carpeta SDD calculada y persiste el resultado como
`BASELINE_AUDIT.md`. Debe incluir comandos exactos, exit codes, alcance auditado, riesgos, supuestos
y gaps. Desde ese momento, cada cambio del árbol debe ser atribuible a esta ejecución.

Gate G2 — BASELINE PASS: auditoría con evidencia, comandos canónicos descubiertos, suite baseline
obligatoria verde y no mutante, sin blocker crítico sin resolver.

FASE 3 — BOOTSTRAP SDD LOCAL Y ESPECIFICACIÓN

1. Si existe SDD, utiliza sus plantillas, estados y skills. No sobrescribas artefactos humanos.
2. Si falta SDD y `LOCAL_SDD_BOOTSTRAP` está permitido, crea solo dentro de la rama los artefactos
   locales mínimos requeridos por el adaptador. Usa onboarding/proyecto-init cuando estén
   disponibles, infiere convenciones desde el repo y marca los hechos humanos desconocidos como
   supuestos conservadores. No instales ni cambies configuración global, no adoptes Graphify ni
   herramientas externas sin autorización previa.
3. Completa la feature numerada `specs/features/<nnn>-<slug>/` ya iniciada por la auditoría, sin
   reutilizar números, con `SPEC.md`, `PLAN.md`, `TASKS.md`, `DECISIONS.md` y
   `BASELINE_AUDIT.md`.
4. SPEC debe contener problema, objetivo, alcance, fuera de alcance, requisitos funcionales y no
   funcionales, seguridad/privacidad/rendimiento/accesibilidad cuando apliquen, edge cases,
   dependencias, riesgos, supuestos y criterios `AC-XXX` observables.
5. Resuelve preguntas técnicas reversibles mediante evidencia y registra la decisión Accepted en
   `DECISIONS.md`, indicando que fue tomada autónomamente. Las preguntas de HUMAN GATE permanecen
   abiertas y detienen el trabajo dependiente.
6. PLAN debe reflejar la arquitectura real, incluir una lista de lectura acotada, estrategia de
   pruebas, compatibilidad, migración y rollback cuando apliquen, y todos los comandos de
   verificación obligatorios.
7. TASKS debe usar IDs estables `T001...`; cada tarea pequeña incluye `Covers: AC-XXX`, archivos o
   límites permitidos y un `Verify:` comprobable. No dejes decisiones arquitectónicas abiertas.
8. Ejecuta clarificación y análisis/guardrails SDD. Corrige contradicciones entre SPEC, PLAN, TASKS
   y DECISIONS antes de implementar. El estado debe llegar mediante el skill propietario a `Ready`.
9. Haz un commit solo de la auditoría y artefactos SDD de preparación, con paths explícitos. Verifica
   después que el árbol está limpio. Este commit prepara la entrada segura al bucle autónomo.

Gate G3 — SPEC READY: cero contradicciones bloqueantes; todos los requisitos tienen AC; todas las
tareas cubren AC y tienen Verify; cero decisiones bloqueantes; estado `Ready`; baseline todavía
verde; commit preparatorio atribuible y árbol limpio.

FASE 4 — IMPLEMENTACIÓN AUTÓNOMA SDD

Si está disponible, ejecuta el contrato equivalente a:

`sdd-orchestrate --autonomous specs/features/<nnn>-<slug> --max-iterations 3`

En Claude usa delegación nativa conforme al adaptador. En Codex, si no hay fan-out o permisos
aislados, ejecuta el mismo protocolo secuencial con `ORCHESTRATION.md` como blackboard durable. La
ausencia de un nombre de comando no omite el contrato: reproduce sus gates con las instrucciones
locales y este prompt.

Reglas del bucle:

1. Procesa una tarea runnable cada vez. Paraleliza únicamente tareas que no comparten archivos,
   contratos, estado, migraciones ni tests conflictivos.
2. Implementa verticalmente y con pruebas por la interfaz pública. Para bugs, reproduce primero.
   Para comportamiento nuevo, crea una prueba roja significativa antes o junto al mínimo cambio.
3. Edita solo los paths permitidos por la tarea. Una necesidad fuera de límite exige actualizar
   SPEC/PLAN mediante su lifecycle correcto y volver a analizar, no improvisar.
4. Tras cada tarea, valida su `Verify:`, los tests focalizados y el diff real antes de marcarla.
5. Ejecuta domain review sobre cada diff implementado. Ejecuta security review si toca auth,
   autorización, datos personales, multi-tenant, pagos, secretos, uploads, API pública, esquema,
   migraciones o persistencia.
6. Convierte cada hallazgo confirmado en una única tarea trazable, repárala y exige re-aprobación
   del reviewer sobre el fingerprint actual. Cualquier cambio invalida aprobaciones de fingerprints
   anteriores.
7. Usa severidades cerradas `Critical | High | Medium | Low`, IDs estables y evidencia concreta.
   Nunca rebajes silenciosamente un finding.
8. Aplica límite de iteración al estancamiento, no al volumen legítimo de trabajo. Tres rechazos del
   mismo finding después de reparaciones sin progreso activan HUMAN GATE. Mantén además un presupuesto
   de delegaciones al menos `max(25, 6 × tareas inicialmente pendientes)`.
9. El bucle SDD no hace commit, push, merge, despliegue, migración real ni gestión de secretos. Esas
   acciones siguen perteneciendo a las fases exteriores autorizadas de este prompt.

Gate G4 — IMPLEMENTATION DONE: todas las tareas verificadas, ningún finding abierto, ningún cambio
fuera de scope y ORCHESTRATION registra un resultado convergente.

FASE 5 — GATES FINALES DE CALIDAD Y RIESGO

Ejecuta siempre:

- revisión contra SPEC/PLAN/TASKS/DECISIONS y trazabilidad AC → tarea → prueba;
- QA funcional, edge cases y regresiones;
- formatter/check, lint, typecheck, tests y build que mande PLAN/CI;
- `git diff --check` y revisión completa desde merge-base;
- búsqueda de secretos por una herramienta ya configurada o por patrones seguros que no impriman
  valores; revisión de archivos grandes/binarios inesperados y cambios de dependencias/lockfile;
- final-conformance review independiente sobre el fingerprint completo.

Añade solo los gates cuyo trigger se cumpla:

- database: esquema, migration, entidad, repositorio, query, índice o persistencia;
- API: endpoint, DTO, evento o contrato público;
- performance: hot path, query pesada, loop/render masivo, caché o proceso async;
- frontend/accessibility: UI, estados loading/error/empty, navegación o interacción;
- privacy: datos personales, consentimiento, retención, logging o borrado;
- backend/framework/domain: según stack y perfil detectados;
- deployment/container/pipeline: si el diff toca sus artefactos. `release-readiness` solo corresponde
  a un release/deploy real, que este prompt no autoriza.

Un gate rechazado crea una tarea de reparación, vuelve a la fase 4 y después repite todos los gates
afectados. Ningún warning se ignora sin registrar el motivo y demostrar que no bloquea los AC.

Gate G5 — QUALITY PASS: suite completa verde, reviews aplicables en APPROVE/PASS sobre el fingerprint
actual, cero Critical/High/Medium/Low abiertos, cero secretos y cero cambios inesperados.

FASE 6 — CIERRE SDD

1. Congela el fingerprint aprobado de implementación.
2. Ejecuta el lifecycle propietario de spec-review; solo este puede pasar a `In Review`.
3. Ejecuta QA y reviews especializadas finales requeridas.
4. Ejecuta spec-close; solo este puede pasar a `Done`.
5. Genera `PR_DESCRIPTION.md` desde el diff y los artefactos SDD. Debe enumerar todos los AC, tests
   ejecutados, decisiones, riesgos y follow-ups reales.
6. Audita el delta de cierre: solo se permiten cambios de estado/evidencia SDD y descripción de PR.
   Si cambió producción, tests, requisitos, PLAN/TASKS sustantivos o DECISIONS, invalida conformidad y
   vuelve al gate correspondiente.

Gate G6 — SDD CLOSED: SPEC `Done`, todas las tareas checked, cero preguntas/escalaciones/findings
abiertos, PR_DESCRIPTION completa y delta de cierre exclusivamente administrativo/evidencial.

FASE 7 — COMMIT Y PUBLICACIÓN SEGURA

1. Revisa `git status` y el diff completo. Atribuye cada path a una tarea/AC o retíralo del alcance
   mediante una edición explícita; no uses comandos destructivos para limpiar.
2. Ejecuta de nuevo los checks que un commit puede afectar (format/lint/tests pertinentes).
3. Stagea paths explícitos; nunca `git add .` ni `git add -A`. Verifica el staged diff y que no
   contiene secretos, artefactos generados accidentales, datos locales o binarios inesperados.
4. Crea commits coherentes siguiendo la convención del repositorio. No uses `--no-verify`. Si la
   firma obligatoria requiere intervención, HUMAN GATE.
5. Verifica árbol limpio y vuelve a ejecutar la suite final desde el commit, no desde cambios sin
   commit.
6. Haz fetch de la rama por defecto. Si avanzó, integra sus cambios sin reescribir historia
   publicada: antes del primer push se permite rebase solo si todos los commits son atribuibles a
   esta ejecución; después de publicar, usa merge. Resuelve conflictos dentro de scope y repite G5
   y G6. Si la procedencia es ambigua, HUMAN GATE.
7. Publica exclusivamente la rama de la feature con un push normal y upstream explícito. Nunca
   force push, tags, otras ramas ni el branch por defecto.

Gate G7 — PUBLISHABLE: commits atribuibles, árbol limpio, suite verde desde HEAD, branch actualizado
con la base, push normal exitoso y diff remoto idéntico al aprobado.

FASE 8 — PULL REQUEST, CI REMOTO Y CONVERGENCIA

1. Crea la Pull Request inicialmente como DRAFT, desde la rama de feature hacia la rama por defecto,
   usando el template del repositorio y `PR_DESCRIPTION.md`. Sigue la convención local de título y
   enlaza la carpeta de spec. No asignes reviewers ni notifiques personas salvo que las reglas del
   repositorio lo exijan explícitamente.
2. Captura y valida URL, número, base, head y lista exacta de commits/archivos. Si ya existe una PR
   para esa rama, actualiza esa PR; no dupliques.
3. Espera los checks requeridos con la herramienta disponible. Distingue fallo de código, flaky e
   infraestructura/permisos.
4. Ante fallo atribuible al cambio: reproduce localmente, crea tarea/hallazgo trazable, corrige,
   repite G5–G7, haz commit y push normales, actualiza la PR y vuelve a esperar CI.
5. Ante flaky confirmado, permite como máximo un rerun si el proveedor lo autoriza y registra la
   evidencia. No uses reruns para ocultar un fallo determinista.
6. Ante fallo externo o falta de permisos que no puede corregirse en el repo, conserva la PR como
   DRAFT, documenta el blocker y activa HUMAN GATE con la acción mínima necesaria.
7. Repite como máximo `MAX_CI_REPAIR_ITERATIONS` por el mismo fallo. El límite detecta estancamiento;
   un fallo nuevo conserva su identidad propia pero no permite un bucle sin límite.
8. Cuando todos los checks requeridos estén verdes y G0–G7 sigan vigentes, marca la PR como ready
   for review. No hagas merge ni actives auto-merge.

Gate G8 — DELIVERY COMPLETE: PR única y lista, checks requeridos verdes, head remoto igual al HEAD
aprobado, SPEC Done y ninguna escalación abierta. El trabajo termina aquí, sin merge ni deploy.

PROTOCOLO DE INCIDENTE DE SECRETOS

Si un secreto nuevo aparece solo en cambios no publicados: no lo muestres, retíralo mediante una
edición explícita, añade una prevención adecuada y repite los gates. Si parece preexistente,
versionado o ya publicado: no reescribas historia ni intentes rotarlo; conserva evidencia sin el
valor y activa HUMAN GATE para que el propietario coordine revocación/rotación.

INFORME FINAL OBLIGATORIO

Solo declara COMPLETE si G8 está satisfecho. Responde de forma compacta con:

- resultado: COMPLETE | HUMAN GATE REQUIRED;
- URL y número de PR, rama base/head y estado draft/ready;
- feature path y estado SDD;
- resumen de cambios y commits;
- tabla G0–G8 con PASS/FAIL y evidencia breve;
- comandos/tests ejecutados y resultado;
- reviews activadas y veredictos;
- supuestos, riesgos y follow-ups;
- confirmación explícita: no merge, no deploy, no auto-merge, no force push.

Empieza ahora por FASE 0 y continúa de manera autónoma hasta satisfacer G8 o encontrar un HUMAN
GATE real. No cierres una respuesta prometiendo continuar después: ejecuta el siguiente paso seguro
en la misma sesión.
```

## Fin del prompt

### Preparación recomendada de los adaptadores

El prompt no debe instalar ni modificar configuración global durante una entrega. Haz esa preparación
una sola vez, fuera de la sesión autónoma, con el instalador dual de este repositorio:

| Plataforma | Preview | Instalación de Claude + Codex para el proyecto |
|---|---|---|
| Cualquiera, como plugin (recomendado) | `claude plugin details sdd` tras añadir el marketplace | `claude plugin marketplace add <repo>` + `claude plugin install sdd@spec-driven-development`; en Codex, `codex plugin marketplace add <repo>` + `codex plugin add sdd@spec-driven-development` |
| macOS | `./install-all.sh --dry-run --link-user-claude --codex-target /ruta/al/proyecto` | `./install-all.sh --link-user-claude --codex-target /ruta/al/proyecto` |
| Windows PowerShell | `.\install-all.ps1 -DryRun -LinkUserClaude -CodexTarget C:\ruta\al\proyecto` | `.\install-all.ps1 -LinkUserClaude -CodexTarget C:\ruta\al\proyecto` |

Con el plugin, los hooks ya están conectados en cada proyecto donde esté activo y este paso sobra;
no lo combines con el plugin o cada hook disparará dos veces. Con el instalador, para que **Claude
Code** tenga guardrails mecánicos dentro del proyecto, conecta los hooks después de revisar primero
el dry-run:

| Plataforma | Preview | Aplicación |
|---|---|---|
| macOS | `./scripts/wire-hooks.sh --dry-run --project-dir /ruta/al/proyecto` | `./scripts/wire-hooks.sh --project-dir /ruta/al/proyecto` |
| Windows PowerShell | `.\scripts\wire-hooks.ps1 -DryRun -ProjectDir C:\ruta\al\proyecto` | `.\scripts\wire-hooks.ps1 -ProjectDir C:\ruta\al\proyecto` |

En Codex, los guardrails del adaptador siguen siendo convenciones del prompt y `AGENTS.md`, no hooks
deterministas. Por eso el prompt hace cada gate explícito y exige evidencia antes de permitir la
publicación.
