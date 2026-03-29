import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { SettingsComponent } from './settings/settings.component';
import { StaffFormComponent } from './settings/staff-form/staff-form.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'settings', component: SettingsComponent },
  { path: 'settings/staff/new', component: StaffFormComponent },
  { path: 'settings/staff/:id', component: StaffFormComponent },
  { path: '**', redirectTo: '' },
];
