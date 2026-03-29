import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { AccessService } from '../services/access.service';
import { StaffService, StaffRecord } from '../services/staff.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSnackBarModule,
    MatToolbarModule,
  ],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.css',
})
export class SettingsComponent implements OnInit {
  // Access code
  currentCode = '';
  newCode = '';
  codeError: string | null = null;
  isUpdatingCode = false;

  // Staff
  staffList: StaffRecord[] = [];
  isLoadingStaff = false;

  constructor(
    private router: Router,
    private accessService: AccessService,
    private staffService: StaffService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadStaff();
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  // --- Access Code ---

  get isCodeValid(): boolean {
    return (
      this.currentCode.length >= 4 &&
      this.newCode.length >= 4 &&
      /^\d+$/.test(this.newCode)
    );
  }

  updateCode(): void {
    if (!this.isCodeValid || this.isUpdatingCode) return;

    this.codeError = null;
    this.isUpdatingCode = true;

    this.accessService.updateCode(this.currentCode, this.newCode).subscribe({
      next: (response) => {
        this.snackBar.open(response.message, 'OK', {
          duration: 4000,
          panelClass: ['snackbar-success'],
        });
        this.currentCode = '';
        this.newCode = '';
        this.isUpdatingCode = false;
      },
      error: (err: HttpErrorResponse) => {
        this.codeError = err.error?.message || 'An error occurred.';
        this.isUpdatingCode = false;
      },
    });
  }

  // --- Staff Management ---

  loadStaff(): void {
    this.isLoadingStaff = true;
    this.staffService.listStaff().subscribe({
      next: (response) => {
        this.staffList = response.data || [];
        this.isLoadingStaff = false;
      },
      error: () => {
        this.isLoadingStaff = false;
      },
    });
  }

  addStaff(): void {
    this.router.navigate(['/settings/staff/new']);
  }

  editStaff(staffId: string): void {
    this.router.navigate(['/settings/staff', staffId]);
  }
}
