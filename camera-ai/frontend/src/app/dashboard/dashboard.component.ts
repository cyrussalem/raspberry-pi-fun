import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { environment } from '../../environments/environment';
import { KeypadDialogComponent } from '../dialogs/keypad-dialog/keypad-dialog.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatDialogModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent {
  readonly streamUrl = `${environment.apiBaseUrl}/api/video/stream`;

  readonly buttons = [
    { label: 'Door Pin', icon: 'dialpad' },
    { label: 'Settings', icon: 'settings' },
    { label: 'Snapshot', icon: 'photo_camera' },
    { label: 'Record', icon: 'videocam' },
    { label: 'Fullscreen', icon: 'fullscreen' },
    { label: 'Info', icon: 'info' },
  ];

  constructor(private dialog: MatDialog, private router: Router) {}

  onButtonClick(label: string): void {
    switch (label) {
      case 'Door Pin':
        this.dialog.open(KeypadDialogComponent, {
          width: '520px',
          panelClass: 'dark-dialog',
        });
        break;
      case 'Settings':
        this.router.navigate(['/settings']);
        break;
    }
  }
}
