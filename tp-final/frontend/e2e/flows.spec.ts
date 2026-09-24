import { expect, type Page, test } from '@playwright/test'

// One ordered story over a fresh database (start-api.sh recreates it on every run).
test.describe.configure({ mode: 'serial' })

async function login(page: Page, name: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Usuario').fill(name)
  await page.getByLabel('Contraseña', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await page.waitForURL((url) => url.pathname !== '/login')
}

test('forced password change on first admin login', async ({ page }) => {
  await login(page, 'admin', 'Proyecto1')
  await expect(page).toHaveURL(/\/password$/)
  await expect(page.getByText('reemplazá tu contraseña inicial')).toBeVisible()
  await page.goto('/proyectos') // blocked until the password is changed
  await expect(page).toHaveURL(/\/password$/)
  await page.getByLabel('Contraseña actual').fill('Proyecto1')
  await page.getByLabel('Nueva contraseña', { exact: true }).fill('AdminNueva1')
  await page.getByLabel('Confirmar nueva contraseña').fill('AdminNueva1')
  await page.getByRole('button', { name: 'Guardar contraseña' }).click()
  await expect(page).toHaveURL(/\/proyectos$/)
  await expect(page.getByText('Contraseña actualizada.')).toBeVisible()
})

test('admin creates a user, a role and a project', async ({ page }) => {
  await login(page, 'admin', 'AdminNueva1')
  await page.getByRole('link', { name: 'Recursos' }).click()
  await page.getByRole('link', { name: '+ Nuevo recurso' }).click()
  await page.getByLabel('Nombre de usuario').fill('ana')
  await page.getByLabel('Email (opcional)').fill('ana@example.com')
  await page.getByLabel('Contraseña inicial').fill('Inicial123')
  await page.getByRole('button', { name: 'Guardar' }).click()
  await expect(page.getByRole('cell', { name: 'ana' })).toBeVisible()

  await page.getByRole('link', { name: 'Roles' }).click()
  await page.getByRole('link', { name: '+ Nuevo rol' }).click()
  await page.getByLabel('Descripción del rol').fill('Analista')
  await page.getByRole('button', { name: 'Guardar' }).click()
  await expect(page.getByRole('cell', { name: 'Analista' })).toBeVisible()

  await page.getByRole('link', { name: 'Proyectos', exact: true }).click()
  await page.getByRole('link', { name: '+ Nuevo proyecto' }).click()
  await page.getByLabel('Nombre del proyecto').fill('Portal <b>clientes</b>')
  await page.getByLabel('Fecha de inicio').fill('2026-09-01')
  await page.getByLabel('Fecha de fin prevista').fill('2026-09-30')
  await page.getByLabel('Horas requeridas').fill('20')
  await page.getByLabel('Avance real (%)').fill('40')
  await page.getByLabel('Responsable').selectOption({ label: 'ana' })
  await page.getByLabel('Estado').selectOption('en curso')
  await page.getByRole('button', { name: 'Guardar' }).click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Portal <b>clientes</b>') // escaped
  await expect(page.getByText('ana · 2026-09-01 → 2026-09-30 · en curso')).toBeVisible()
})

test('plain user logs hours; invalid input keeps the form', async ({ page }) => {
  await login(page, 'ana', 'Inicial123')
  await page.getByLabel('Contraseña actual').fill('Inicial123')
  await page.getByLabel('Nueva contraseña', { exact: true }).fill('AnaPropia12')
  await page.getByLabel('Confirmar nueva contraseña').fill('AnaPropia12')
  await page.getByRole('button', { name: 'Guardar contraseña' }).click()
  await expect(page).toHaveURL(/\/proyectos$/)
  await expect(page.getByRole('link', { name: 'Recursos' })).toHaveCount(0) // admin-only nav hidden

  await page.getByRole('link', { name: 'Ver proyecto →' }).click()
  await page.getByRole('link', { name: '+ Registrar consumo' }).click()
  await expect(page.getByText('Recurso: ana')).toBeVisible()
  await page.getByLabel('Rol desempeñado').selectOption({ label: 'Analista' })
  await page.getByLabel('Tarea realizada').fill('Relevamiento')
  await page.getByLabel('Fecha de inicio').fill('2026-10-02')
  await page.getByLabel('Fecha de fin').fill('2026-10-01')
  await page.getByLabel('Horas consumidas').fill('25.5')
  await page.getByRole('button', { name: 'Guardar' }).click()
  await expect(page.getByRole('alert')).toHaveText('La fecha de fin no puede ser anterior al inicio.')
  await expect(page.getByLabel('Tarea realizada')).toHaveValue('Relevamiento') // input preserved

  await page.getByLabel('Fecha de fin').fill('2026-10-03')
  await page.getByRole('button', { name: 'Guardar' }).click()
  await expect(page.getByText('Cambios guardados.')).toBeVisible()
  // 25,5 h over 20 h: overrun of 5,5 h; manual progress unchanged.
  await expect(page.getByText('-5,5 / 5,5')).toBeVisible()
  await expect(page.getByText('40 %').first()).toBeVisible()

  await page.goto('/recursos') // admin route: redirected
  await expect(page).toHaveURL(/\/proyectos$/)
  await page.getByRole('button', { name: 'Salir' }).click()
  await expect(page).toHaveURL(/\/login$/)
})

test('reloading a deep link keeps the session', async ({ page }) => {
  await login(page, 'admin', 'AdminNueva1')
  await page.goto('/proyectos/1')
  await page.reload()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Portal <b>clientes</b>')
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('row', { name: /Relevamiento/ }).getByRole('button', { name: 'Eliminar' }).click()
  await expect(page.getByText('Registro eliminado.')).toBeVisible()
  await expect(page.getByText('Todavía no hay consumos registrados.')).toBeVisible()
})
